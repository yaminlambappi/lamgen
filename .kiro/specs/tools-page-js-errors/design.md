# tools-page-js-errors Bugfix Design

## Overview

Three JavaScript errors break tool pages on load. The root causes are:

1. **Script ordering bug** (`registerToolData is not defined`): `tool_base.html` overrides `{% block extra_js %}` and nests `{% block tool_js %}` inside it. In `base.html`, the render order is `{% block extra_js %}` → `tool-runtime.js` → `{% block tool_js %}`. Because `tool_base.html` places `{% block tool_js %}` inside its `extra_js` override, the tool script (which calls `registerToolData`) executes before `tool-runtime.js` is loaded. Fix: move the `<script src="tool-runtime.js">` tag in `base.html` to before `{% block extra_js %}`, or restructure `tool_base.html` so `{% block tool_js %}` is not nested inside `{% block extra_js %}`.

2. **Duplicate `let indentSize` in xml-formatter**: The `{% block tool_js %}` script in `xml-formatter.html` declares `let indentSize = 2;` twice in the same script scope, causing a `SyntaxError` on parse.

3. **Duplicate `const BREAK_BEFORE` in sql-beautifier**: The `{% block tool_js %}` script in `sql-beautifier.html` declares `const BREAK_BEFORE` twice in the same script scope, causing a `SyntaxError` on parse.

The fix strategy is minimal: (1) reorder the `tool-runtime.js` script tag in `base.html` to load before `{% block extra_js %}`; (2) remove the duplicate `let indentSize` declaration in `xml-formatter.html`; (3) remove the duplicate `const BREAK_BEFORE` declaration in `sql-beautifier.html`.

## Glossary

- **Bug_Condition (C)**: The set of conditions that trigger one of the three JavaScript errors on page load
- **Property (P)**: The desired behavior — tool pages load without JavaScript errors and tool functionality works
- **Preservation**: Existing tool behavior (formatting, data registration, UI interactions) that must remain unchanged after the fix
- **`registerToolData`**: Function defined in `static/js/tool-runtime.js` that registers tool data into `window.LamGenTools`
- **`getToolData`**: Function defined in `static/js/tool-runtime.js` that retrieves registered tool data
- **`{% block tool_js %}`**: Django template block in `tool_base.html` (nested inside `{% block extra_js %}`) where individual tool scripts are placed
- **`{% block extra_js %}`**: Django template block in `base.html` that renders before `tool-runtime.js` is loaded
- **Script execution order**: The sequence in which `<script>` tags are parsed and executed by the browser — inline scripts execute synchronously in DOM order

## Bug Details

### Bug Condition

The bug manifests under three distinct conditions, all triggered on page load:

**Bug 1 — Script ordering**: Any tool template that calls `registerToolData()` inside `{% block tool_js %}` will fail because `tool_base.html` nests `{% block tool_js %}` inside `{% block extra_js %}`, and `base.html` loads `tool-runtime.js` after `{% block extra_js %}`. The rendered HTML has the tool script executing before `window.registerToolData` is defined.

**Bug 2 — Duplicate `let indentSize`**: The xml-formatter template declares `let indentSize = 2;` twice in the same `<script>` block scope.

**Bug 3 — Duplicate `const BREAK_BEFORE`**: The sql-beautifier template declares `const BREAK_BEFORE` twice in the same `<script>` block scope.

**Formal Specification:**
```
FUNCTION isBugCondition(pageLoad)
  INPUT: pageLoad — { template: string, scriptContent: string }
  OUTPUT: boolean

  IF pageLoad.template extends tool_base.html
     AND pageLoad.scriptContent calls registerToolData()
     AND tool-runtime.js is not yet loaded when scriptContent executes
  THEN RETURN true   -- Bug 1: ReferenceError

  IF pageLoad.template == 'xml-formatter.html'
     AND occurrences('let indentSize', pageLoad.scriptContent) > 1
  THEN RETURN true   -- Bug 2: SyntaxError indentSize

  IF pageLoad.template == 'sql-beautifier.html'
     AND occurrences('const BREAK_BEFORE', pageLoad.scriptContent) > 1
  THEN RETURN true   -- Bug 3: SyntaxError BREAK_BEFORE

  RETURN false
END FUNCTION
```

### Examples

- **json-formatter page load** → `Uncaught ReferenceError: registerToolData is not defined` at line where `registerToolData('jsonFormatter', {...})` is called; tool is non-functional
- **xml-formatter page load** → `Uncaught ReferenceError: registerToolData is not defined` (Bug 1) AND `Uncaught SyntaxError: Identifier 'indentSize' has already been declared` (Bug 2); Format button does nothing
- **sql-beautifier page load** → `Uncaught SyntaxError: Identifier 'BREAK_BEFORE' has already been declared`; Format and Minify buttons do nothing
- **Any other tool using `registerToolData`** (html-formatter, yaml-formatter, js-formatter, css-formatter, markdown-previewer) → same ReferenceError as Bug 1

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `registerToolData(toolName, data)` must continue to store data at `window.LamGenTools[toolName]`
- `getToolData(toolName, defaultValue)` must continue to return `window.LamGenTools[toolName]` or the default
- Mouse clicks on Format/Minify/Copy/Download buttons must continue to work exactly as before
- xml-formatter `setIndent(btn, size)` must continue to update `indentSize` and re-format output
- sql-beautifier `BREAK_BEFORE` set must continue to drive SQL keyword line-breaking in `formatSql()`
- json-formatter formatting, validation, and display must remain unchanged
- All tool pages that do NOT call `registerToolData` must be completely unaffected by the fix
- The `{% block tool_js %}` block in `base.html` must continue to work for tools that use it directly (not via `tool_base.html`)

**Scope:**
All inputs and interactions that do NOT involve the buggy page-load script execution order or the duplicate declarations are completely unaffected. This includes:
- All user interactions after page load (button clicks, keyboard shortcuts, textarea input)
- All tool pages that don't call `registerToolData`
- The `tool-runtime.js` API itself (no changes to `registerToolData` or `getToolData` logic)

## Hypothesized Root Cause

### Bug 1 — `registerToolData is not defined`

The rendering chain is:

```
base.html renders:
  ...
  {% block extra_js %}          ← tool_base.html fills this
    [tool_base.html extra_js content including bookmark/FAQ scripts]
    {% block tool_js %}         ← individual tool fills this
      <script>
        registerToolData(...)   ← executes HERE (tool-runtime.js not yet loaded)
      </script>
    {% endblock %}
  {% endblock %}
  <script src="tool-runtime.js">  ← loaded AFTER extra_js block
  {% block tool_js %}{% endblock %} ← base.html's own tool_js (empty for tool pages)
```

The fix is to move `<script src="tool-runtime.js">` in `base.html` to before `{% block extra_js %}`, so it is always available when any script in `extra_js` or `tool_js` runs.

### Bug 2 — Duplicate `let indentSize` in xml-formatter

The `{% block tool_js %}` script in `xml-formatter.html` contains two consecutive `let indentSize = 2;` declarations in the same script scope. `let` does not allow re-declaration in the same scope, so the browser throws a `SyntaxError` before any code in the script executes.

### Bug 3 — Duplicate `const BREAK_BEFORE` in sql-beautifier

The `{% block tool_js %}` script in `sql-beautifier.html` contains two consecutive `const BREAK_BEFORE = new Set([...])` declarations in the same script scope. `const` does not allow re-declaration in the same scope, so the browser throws a `SyntaxError` before any code in the script executes.

## Correctness Properties

Property 1: Bug Condition — Tool Scripts Execute After tool-runtime.js Is Loaded

_For any_ tool page where `registerToolData()` is called inside `{% block tool_js %}` (i.e., isBugCondition returns true for Bug 1), the fixed template structure SHALL ensure `tool-runtime.js` is loaded before the tool script executes, so `registerToolData` is defined and no `ReferenceError` is thrown.

**Validates: Requirements 2.1, 2.4**

Property 2: Preservation — Non-Buggy Tool Pages and Interactions Unchanged

_For any_ tool page or user interaction where the bug condition does NOT hold (isBugCondition returns false), the fixed code SHALL produce exactly the same behavior as the original code, preserving all existing functionality including `registerToolData`/`getToolData` semantics, formatting logic, and UI interactions.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**Fix 1 — Script ordering**

**File**: `templates/base.html`

**Change**: Move `<script src="{% static 'js/tool-runtime.js' %}">` to before `{% block extra_js %}{% endblock %}`.

**Before:**
```html
{% block extra_js %}{% endblock %}
<script src="{% static 'js/tool-runtime.js' %}"></script>
```

**After:**
```html
<script src="{% static 'js/tool-runtime.js' %}"></script>
{% block extra_js %}{% endblock %}
```

This ensures `window.registerToolData` and `window.getToolData` are defined before any inline script in `extra_js` or `tool_js` runs.

---

**Fix 2 — Duplicate `let indentSize`**

**File**: `templates/tools/developer/xml-formatter.html`

**Change**: Remove the second `let indentSize = 2;` declaration, keeping only one.

---

**Fix 3 — Duplicate `const BREAK_BEFORE`**

**File**: `templates/tools/developer/sql-beautifier.html`

**Change**: Remove the second `const BREAK_BEFORE = new Set([...])` declaration, keeping only one.

---

### Specific Changes Summary

1. **`templates/base.html`**: Swap the order of `<script src="tool-runtime.js">` and `{% block extra_js %}` so the runtime loads first
2. **`templates/tools/developer/xml-formatter.html`**: Delete the duplicate `let indentSize = 2;` line
3. **`templates/tools/developer/sql-beautifier.html`**: Delete the duplicate `const BREAK_BEFORE = new Set([...])` line

No changes to `tool-runtime.js`, no changes to any Python/Django view code, no changes to any other template.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis.

**Test Plan**: Write tests that simulate the script execution environment (tool-runtime.js not yet loaded) and assert that calling `registerToolData` throws a `ReferenceError`. Also write tests that parse the template script content and detect duplicate `let`/`const` declarations.

**Test Cases**:
1. **Script Order Test**: Simulate calling `registerToolData('test', {})` in an environment where `tool-runtime.js` has not been loaded — assert `ReferenceError` is thrown (will fail on unfixed code, pass after fix)
2. **xml-formatter Duplicate Declaration Test**: Parse `xml-formatter.html` script content and assert `let indentSize` appears exactly once (will fail on unfixed code)
3. **sql-beautifier Duplicate Declaration Test**: Parse `sql-beautifier.html` script content and assert `const BREAK_BEFORE` appears exactly once (will fail on unfixed code)
4. **Post-fix registerToolData Test**: After fix, simulate calling `registerToolData('test', {examples: {}})` and assert no error is thrown and `window.LamGenTools.test` is set

**Expected Counterexamples**:
- `registerToolData` call throws `ReferenceError: registerToolData is not defined` when tool-runtime.js is not loaded
- `let indentSize` count in xml-formatter script block is 2 (should be 1)
- `const BREAK_BEFORE` count in sql-beautifier script block is 2 (should be 1)

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed code produces the expected behavior.

**Pseudocode:**
```
FOR ALL toolPage WHERE isBugCondition(toolPage) DO
  result := loadPage_fixed(toolPage)
  ASSERT noJavaScriptErrors(result)
  ASSERT toolFunctionality(result) works
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed code produces the same result as the original code.

**Pseudocode:**
```
FOR ALL toolPage WHERE NOT isBugCondition(toolPage) DO
  ASSERT loadPage_original(toolPage) == loadPage_fixed(toolPage)
END FOR

FOR ALL userInteraction WHERE NOT isBugCondition(userInteraction) DO
  ASSERT originalBehavior(userInteraction) == fixedBehavior(userInteraction)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that `registerToolData`/`getToolData` semantics are unchanged for all valid inputs

**Test Plan**: Observe behavior of `registerToolData`, `getToolData`, `formatXML`, `formatSql` on unfixed code (for non-buggy inputs), then write tests capturing that behavior.

**Test Cases**:
1. **registerToolData Preservation**: Verify `registerToolData('foo', {x:1})` stores `{x:1}` at `window.LamGenTools.foo` — same before and after fix
2. **getToolData Preservation**: Verify `getToolData('foo', null)` returns registered data — same before and after fix
3. **xml-formatter setIndent Preservation**: Verify `setIndent(btn, 4)` sets `indentSize` to 4 and re-formats output correctly
4. **sql-beautifier BREAK_BEFORE Preservation**: Verify `formatSql()` with `SELECT id FROM users` produces line breaks before `FROM`

### Unit Tests

- Test that `base.html` renders `tool-runtime.js` script tag before `{% block extra_js %}` content
- Test that xml-formatter script block contains exactly one `let indentSize` declaration
- Test that sql-beautifier script block contains exactly one `const BREAK_BEFORE` declaration
- Test `registerToolData` with valid tool name and data object — verifies storage in `window.LamGenTools`
- Test `getToolData` with registered and unregistered tool names — verifies correct return values
- Test `formatXML()` with valid XML input — verifies correct indented output
- Test `formatSql()` with a multi-clause SQL query — verifies keyword line-breaking

### Property-Based Tests

- Generate random tool names and data objects; verify `registerToolData` then `getToolData` round-trips correctly for all inputs
- Generate random valid XML strings; verify `formatXML()` output is well-formed XML with correct indentation for all inputs
- Generate random SQL strings containing keywords from `BREAK_BEFORE`; verify `formatSql()` places each keyword on a new line

### Integration Tests

- Load json-formatter page and verify no console errors, then verify Format button produces valid JSON output
- Load xml-formatter page and verify no console errors, then verify Format button produces indented XML output
- Load sql-beautifier page and verify no console errors, then verify Format button produces line-broken SQL output
- Verify switching indent modes (2 spaces → 4 spaces → tabs) in xml-formatter re-formats output correctly
- Verify that tools not using `registerToolData` (e.g., a simple tool with no data registration) are unaffected by the script order change
