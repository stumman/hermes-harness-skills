/**
 * improve-skill.workflow.js — autonomous champion/challenger skill-improvement swarm.
 *
 * Implements the skill-doctor loop (see ../skills/skill-doctor/SKILL.md) as a bounded,
 * role×phase agent swarm. Reusable for ANY skill — pass the target via `args`.
 *
 * RUN:
 *   Workflow({ scriptPath: ".agents/harness/improve-skill.workflow.js",
 *              args: { skill: "ponytail-audit", maxIters: 5, kTrials: 3,
 *                      targetPassRate: 0.9, editBudget: 1, plateauK: 3, branch: "skills/auto-improve" } })
 *
 * GOVERNANCE: never edits a SKILL.md in place on main. Each kept challenger is one commit on
 * `args.branch`; provenance is appended to an EXTERNAL ledger (docs/skill-changelogs/<skill>.jsonl)
 * and CHANGELOG — never written into the skill. Human merges the branch. (Decision: auto-apply on
 * branch + changelog, human merges.)
 *
 * Workflow scripts have NO shell/fs — every git/python/file action is done by a spawned agent.
 */
export const meta = {
  name: 'improve-skill',
  description: 'Autonomous champion/challenger swarm that improves one Agent Skill with statistical keep-or-revert gating, bounded by a complexity router and token budget',
  phases: [
    { title: 'Setup', detail: 'diagnose (lint) + confirm/scaffold the golden eval set + baseline' },
    { title: 'Improve', detail: 'per iteration: propose → apply → paired eval → judge panel → keep/revert → ledger' },
    { title: 'Report', detail: 'final baseline→best delta, kept/reverted ledger, remaining failures' },
  ],
}

const cfg = {
  skill: (args && args.skill) || null,
  maxIters: (args && args.maxIters) || 5,
  kTrials: (args && args.kTrials) || 3,
  targetPassRate: (args && args.targetPassRate) || 0.9,
  editBudget: (args && args.editBudget) || 1,
  plateauK: (args && args.plateauK) || 3,
  branch: (args && args.branch) || 'skills/auto-improve',
  proposers: (args && args.proposers) || 5, // N≈5: sampling gains are front-loaded; router may shrink
}
if (!cfg.skill) throw new Error('args.skill is required (skill name under .agents/skills/ or a path to SKILL.md)')

const REPO = '/Users/Mansoor/projects/hermes-harness-skills'
const SKILL_DIR = cfg.skill.includes('/') ? cfg.skill.replace(/\/SKILL\.md$/, '') : `${REPO}/.agents/skills/${cfg.skill}`
const SKILL_MD = `${SKILL_DIR}/SKILL.md`
const NAME = SKILL_DIR.split('/').pop()
const LEDGER = `${REPO}/docs/skill-changelogs/${NAME}.jsonl`
const GOLDEN = `${SKILL_DIR}/eval/golden.json`
const DOCTOR = `${REPO}/.agents/skills/skill-doctor`

const GROUND = `
You operate inside the skill-doctor improvement harness for the skill "${NAME}" (${SKILL_MD}).
Authoritative method + rubric: read ${DOCTOR}/SKILL.md and ${DOCTOR}/references/ as needed.
Hard rules: ONE bounded edit per iteration; never edit the eval set; never weaken/delete a discriminating assertion;
prefer a reference-file pointer over inlining; never write version/provenance into SKILL.md; provenance goes to ${LEDGER}.
Bundled tools you should RUN (don't reimplement): ${DOCTOR}/scripts/lint_skill.py, score_paired.py, ledger.py, and ${REPO}/.agents/score.py.
`

// ---------- SCHEMAS ----------
const ROUTE = { type:'object', additionalProperties:false, required:['complexity','proposers','maxIters','rationale','baselinePassRate'],
  properties:{ complexity:{type:'string',enum:['trivial','medium','complex']}, proposers:{type:'number'},
    maxIters:{type:'number'}, rationale:{type:'string'}, baselinePassRate:{type:'number',description:'champion pass-rate on the golden set, 0-1'},
    goldenReady:{type:'boolean'}, notes:{type:'string'} } }

const PROPOSAL = { type:'object', additionalProperties:false, required:['operator','target','editDescription','hypothesis','expectedAssertion'],
  properties:{ operator:{type:'string'}, target:{type:'string',description:'section/line anchor in SKILL.md or a reference file'},
    editDescription:{type:'string',description:'the exact, single bounded change'}, hypothesis:{type:'string',description:'should raise X from A→B because…'},
    expectedAssertion:{type:'string'}, touchesProtectedRegion:{type:'boolean'} } }

const EVALR = { type:'object', additionalProperties:false, required:['side','perPrompt'],
  properties:{ side:{type:'string',enum:['champion','challenger']},
    perPrompt:{type:'array',items:{type:'object',additionalProperties:false,required:['promptId','trials'],
      properties:{ promptId:{type:'string'}, trials:{type:'array',items:{type:'boolean'}}, evidence:{type:'string'} }}} } }

const VERDICT = { type:'object', additionalProperties:false, required:['aspect','keep','confidence','reason'],
  properties:{ aspect:{type:'string'}, keep:{type:'boolean'}, confidence:{type:'number'}, reason:{type:'string'} } }

const DECISION = { type:'object', additionalProperties:false, required:['decision','reasons'],
  properties:{ decision:{type:'string',enum:['keep','revert','crash']}, reasons:{type:'array',items:{type:'string'}},
    pairedMeanDiff:{type:'number'}, ciLow:{type:'number'}, ciHigh:{type:'number'}, regressions:{type:'array',items:{type:'string'}} } }

// ======================================================================
phase('Setup')
// Complexity router FIRST — never default to a big swarm. Also lints champion + confirms golden set.
const route = await agent(`${GROUND}
SETUP + COMPLEXITY ROUTER. Do all of this, then return the schema:
1. Run \`python3 ${DOCTOR}/scripts/lint_skill.py ${SKILL_MD}\` and read its JSON (the structural gate + score).
2. Check for a golden eval set at ${GOLDEN}. If missing, SCAFFOLD one per ${DOCTOR}/references/eval-schema.md: ≥3 stratified, outcome-based cases (happy/edge/near-miss/should-NOT-trigger) with reference solutions and a train/val/test split; write it to ${GOLDEN}. If present, validate it has ≥3 cases and a split.
3. Establish the champion baseline pass-rate by reasoning over the golden set against the CURRENT skill (rough estimate is fine here; precise paired eval happens per-iteration).
4. Ensure git is on branch "${cfg.branch}" (create from current HEAD if needed) so all challenger commits land off main. Do NOT commit anything yet.
5. Classify complexity: trivial (lint clean + baseline high) → recommend few/0 iterations; medium → ~3 proposers; complex (low baseline / many lint failures) → up to ${cfg.proposers} proposers. Cap maxIters ≤ ${cfg.maxIters}.
Return the route.`, { label:'router+setup', phase:'Setup', schema:ROUTE })

const N = Math.max(1, Math.min(cfg.proposers, route.proposers || cfg.proposers))
const ITERS = Math.max(0, Math.min(cfg.maxIters, route.maxIters || cfg.maxIters))
log(`router: ${route.complexity} | baseline≈${(route.baselinePassRate*100).toFixed(0)}% | proposers=${N} | iters=${ITERS}`)

// Fixed operator library — each proposer gets a DISJOINT slice (diversity = anti-redundancy).
const OPERATORS = [
  'add-missing-instruction tied to a specific failing case',
  'strengthen an ignored rule to MUST/imperative, or promote it to the top',
  'move detail OUT of the body into a one-level reference file (token reduction)',
  'delete a never-read file / dead instruction; tighten the description trigger',
  'crossover-merge the best sections of two prior near-miss variants (read the ledger)',
]

const kept = []
let consecutiveReverts = 0

phase('Improve')
for (let i = 0; i < ITERS; i++) {
  if (budget.total && budget.remaining() < 60000) { log(`stopping: token budget nearly exhausted`); break }
  if (consecutiveReverts >= cfg.plateauK) { log(`plateau: ${consecutiveReverts} reverts — escalating to human`); break }

  // ---- PROPOSE: N proposers (disjoint operators) + 1 critic, then pick one ----
  const proposals = (await parallel(
    Array.from({ length: N }, (_, k) => () =>
      agent(`${GROUND}
ITERATION ${i+1}. ANALYZE the champion's failing cases (TRAIN split only) and PROPOSE EXACTLY ONE bounded edit using THIS operator class ONLY: "${OPERATORS[k % OPERATORS.length]}".
Read the ledger ${LEDGER} (if it exists) and NEVER re-propose a buffered reject. Respect edit budget=${cfg.editBudget}. Do not touch any <!-- SLOW_UPDATE --> region. Write a falsifiable hypothesis.`,
        { label:`propose:${i+1}.${k+1}`, phase:'Improve', schema:PROPOSAL })
    )
  )).filter(Boolean).filter(p => !p.touchesProtectedRegion)

  if (!proposals.length) { log(`iter ${i+1}: no valid proposals`); consecutiveReverts++; continue }

  const pick = await agent(`${GROUND}
ITERATION ${i+1}. You are the CRITIC/selector. Here are ${proposals.length} candidate single edits:
${JSON.stringify(proposals, null, 2)}
Select the ONE most likely to produce a CI-significant, regression-free, non-bloating improvement. Reject any that vaguify a fragile step, over-specify an open task, duplicate existing content, or only add tokens. Return the chosen proposal verbatim.`,
    { label:`select:${i+1}`, phase:'Improve', schema:PROPOSAL })

  // ---- APPLY as an immutable challenger commit, then STATIC GATE ----
  const applied = await agent(`${GROUND}
ITERATION ${i+1}. APPLY this single edit to ${NAME}, then gate it:
${JSON.stringify(pick, null, 2)}
Steps: (a) make the edit (Edit/Write); (b) run \`python3 ${DOCTOR}/scripts/lint_skill.py ${SKILL_MD}\` — if gate_pass is false, REVERT the edit (git checkout -- the files) and report applied=false with the lint reasons; (c) if it passes, \`git add -A && git commit\` on branch "${cfg.branch}" with a one-line message naming the operator. Report whether it committed.`,
    { label:`apply:${i+1}`, phase:'Improve',
      schema:{ type:'object', additionalProperties:false, required:['applied','commit','lintScore','detail'],
        properties:{ applied:{type:'boolean'}, commit:{type:'string'}, lintScore:{type:'number'}, detail:{type:'string'} } } })

  if (!applied.applied) { log(`iter ${i+1}: static gate rejected the edit`); consecutiveReverts++; continue }

  // ---- EXECUTE: paired eval, champion vs challenger, k trials each, in parallel ----
  const [champEval, challEval] = await parallel([
    () => agent(`${GROUND}
ITERATION ${i+1}. EXECUTOR (champion). For each prompt in the golden set ${GOLDEN}, run the task as if guided by the PREVIOUS skill version (git show the parent commit's SKILL.md), ${cfg.kTrials} trials each. You ONLY produce/judge outcomes against the case's expected_behavior — assert on OUTCOMES, not tool order. Return per-prompt trial booleans.`,
      { label:`exec:champ:${i+1}`, phase:'Improve', schema:EVALR }),
    () => agent(`${GROUND}
ITERATION ${i+1}. EXECUTOR (challenger). Same golden set ${GOLDEN}, ${cfg.kTrials} trials each, guided by the CURRENT (just-committed) skill. Return per-prompt trial booleans.`,
      { label:`exec:chall:${i+1}`, phase:'Improve', schema:EVALR }),
  ])

  // ---- VERIFY: diverse judge panel across aspects (majority vote) ----
  const ASPECTS = ['instruction-correctness', 'trigger/CSO-accuracy', 'safety + no removed constraints', 'token-efficiency / no bloat']
  const verdicts = (await parallel(ASPECTS.map(a => () =>
    agent(`${GROUND}
ITERATION ${i+1}. JUDGE (aspect: ${a}). Compare champion vs challenger eval evidence below for THIS aspect only. A/B order is randomized; do not favor longer output. You did NOT write the edit.
CHAMPION: ${JSON.stringify(champEval)}
CHALLENGER: ${JSON.stringify(challEval)}
PROPOSAL: ${JSON.stringify(pick)}
Return whether the challenger is at least as good on this aspect.`,
      { label:`judge:${a.split(/[ /]/)[0]}:${i+1}`, phase:'Improve', schema:VERDICT })
  ))).filter(Boolean)
  const panelKeep = verdicts.filter(v => v.keep).length > verdicts.length / 2

  // ---- DECIDE: statistical paired gate via the bundled script ----
  const decision = await agent(`${GROUND}
ITERATION ${i+1}. STATISTICIAN + COMMITTER. Build the score_paired.py input JSON from these paired results and run \`python3 ${DOCTOR}/scripts/score_paired.py\`:
CHAMPION: ${JSON.stringify(champEval)}
CHALLENGER: ${JSON.stringify(challEval)}
VALIDATION/previously-passing ids come from ${GOLDEN}. Judge panel majority = ${panelKeep ? 'KEEP' : 'REVERT'} (panel disagreement → treat as REVERT and note for human review).
FINAL decision = KEEP only if BOTH the paired CI gate says keep AND the panel says keep.
- If KEEP: leave the challenger commit in place; append a provenance entry to ${LEDGER} via \`python3 ${DOCTOR}/scripts/ledger.py append\` (include operator, rationale, scores, decision=keep) and regenerate the CHANGELOG.
- If REVERT: \`git reset --hard\` to the parent commit; append a decision=revert entry to the ledger (this is the rejected-edit buffer).
- If CRASH: try one cheap fix-and-rerun; if still broken, revert and log decision=crash.
Return the final decision.`,
    { label:`decide:${i+1}`, phase:'Improve', schema:DECISION })

  if (decision.decision === 'keep') { kept.push({ iter:i+1, operator:pick.operator, hypothesis:pick.hypothesis, ...decision }); consecutiveReverts = 0; log(`iter ${i+1}: KEEP (Δ=${decision.pairedMeanDiff})`) }
  else { consecutiveReverts++; log(`iter ${i+1}: ${decision.decision.toUpperCase()} — ${(decision.reasons||[])[0]||''}`) }
}

phase('Report')
const report = await agent(`${GROUND}
FINAL REPORT for "${NAME}". Kept changes this run: ${JSON.stringify(kept, null, 2)}.
Read the ledger ${LEDGER} and the current SKILL.md. Produce a concise report: baseline→final pass-rate delta, count of kept vs reverted vs crashed iterations, the remaining top failures with hypotheses for next run, and whether convergence/target/plateau was hit. State that kept changes live on branch "${cfg.branch}" awaiting human merge. No fluff.`,
  { label:'report', phase:'Report' })

return { skill: NAME, branch: cfg.branch, route, kept, report }
