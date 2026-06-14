# Node 22 --experimental-strip-types Compatibility

When generating TypeScript intended to run directly with `node --experimental-strip-types`, avoid these features. They cause `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` or `ERR_MODULE_NOT_FOUND`.

## Unsupported syntax

### Parameter properties
```ts
// ❌ BREAKS
class Foo {
  constructor(private x: string, public readonly y: number) {}
}

// ✅ FIX — separate field declaration + assignment
class Foo {
  private x: string;
  readonly y: number;
  constructor(x: string, y: number) {
    this.x = x;
    this.y = y;
  }
}
```

### `satisfies` operator
```ts
// ❌ BREAKS
return { a: 1, b: 2 } satisfies MyType;

// ✅ FIX — type annotation on variable
const result: MyType = { a: 1, b: 2 };
return result;
```

### Extensionless relative imports
```ts
// ❌ BREAKS (ERR_MODULE_NOT_FOUND)
import { foo } from './bar';

// ✅ FIX — explicit .ts extension
import { foo } from './bar.ts';
```

### `enum` declarations
```ts
// ❌ BREAKS (ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX)
enum Status { PENDING = 'pending', DONE = 'done' }

// ✅ FIX — const object + type alias
export const Status = {
  PENDING: 'pending',
  DONE: 'done',
} as const;
export type Status = (typeof Status)[keyof typeof Status];
```

### `import type` statements ARE SUPPORTED — use them for type-only imports

```ts
// ✅ CORRECT — import type for types that are export type / export interface
import type { Foo, Bar } from './types.ts';
import { Baz } from './types.ts';  // runtime values

// ❌ WRONG — plain import of export type/interface fails
// export type Foo and export interface Bar are stripped by Node.js,
// so they don't exist as runtime exports
import { Foo, Bar } from './types.ts';
// → SyntaxError: does not provide an export named 'Foo'
```

### Inline `type` modifiers in value imports

```ts
// ❌ BREAKS (ERR_INVALID_TYPESCRIPT_SYNTAX)
import { type Foo, Bar } from './types.ts';

// ✅ FIX — split into separate import type + import
import type { Foo } from './types.ts';
import { Bar } from './types.ts';
```

### Import aliases
```ts
// ✅ CORRECT — `import { X as Y }` using `as` IS supported
// This is standard ES module syntax, not TypeScript-specific
import { SagaStatus as SS } from './types.ts';

// ✅ CORRECT — aliases are useful for namespace shortening
import { ErrorCode as EC, FrameType as FT } from './types.ts';

// ❌ WRONG — `import { X: Y }` using `:` is invalid in all JS/TS
import { SagaStatus: SS } from './types.ts';
// → Error: Expected ',' but got ':'
```

## Supported (safe to use)
- All type annotations (`: string`, `: number[]`, generics, etc.)
- `interface`, `type` declarations, `readonly`, `as` casts
- `export type` and `export interface` — stripped at export time; consumers MUST use `import type` to import them
- `import type { X }` statements — correctly stripped by Node.js
- `{ ... } as const` + type alias (enum replacement pattern)
- Async/await, destructuring, template literals
- All ES module syntax

## Detection — error code → likely cause
| Error | Likely cause |
|---|---|
| `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX: TypeScript enum is not supported in strip-only mode` | `enum` keyword |
| `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX: TypeScript parameter property is not supported` | `constructor(public x)` |
| `SyntaxError: The requested module does not provide an export named 'X'` | Plain `import { X }` where X is `export type`/`export interface` (must use `import type { X }`) |
| `ERR_INVALID_TYPESCRIPT_SYNTAX: Unexpected token 'type'` | Inline `type` modifier in value import (`import { type X }`) |
| `ERR_INVALID_TYPESCRIPT_SYNTAX: Expected ',', got ':'` | Import alias (`import { X as Y }`) or `satisfies` |
| `ERR_MODULE_NOT_FOUND: Cannot find module '.../foo'` | Extensionless local import (add `.ts`)
