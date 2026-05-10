# Bugfix Requirements Document

## Introduction

Multiple tool pages throw JavaScript console errors on load, breaking tool functionality for users. The errors fall into two categories: (1) `registerToolData is not defined` — caused by tool scripts calling `registerToolData()` before `tool-runtime.js` is loaded, because `{% block tool_js %}` is nested inside `{% block extra_js %}` in `tool_base.html`, and `base.html` loads `tool-runtime.js` *after* the `extra_js` block; (2) `SyntaxError: Identifier 'X' has already been declared` — caused by duplicate `const`/`let` variable declarations in the same script scope across the xml-formatter and sql-beautifier templates.

Affected pages confirmed: json-formatter, xml-formatter, sql-beautifier. The same script-ordering issue likely affects any tool that calls `registerToolData` inside `{% block tool_js %}`.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a tool page that calls `registerToolData()` inside `{% block tool_js %}` is loaded THEN the system throws `Uncaught ReferenceError: registerToolData is not defined` because `tool-runtime.js` is loaded after the `extra_js` block in `base.html`

1.2 WHEN the xml-formatter page is loaded THEN the system throws `Uncaught SyntaxError: Identifier 'indentSize' has already been declared` because `let indentSize` is declared more than once in the same script scope

1.3 WHEN the sql-beautifier page is loaded THEN the system throws `Uncaught SyntaxError: Identifier 'BREAK_BEFORE' has already been declared` because `const BREAK_BEFORE` is declared more than once in the same script scope

1.4 WHEN any of the above errors occur THEN the system leaves the tool non-functional for the user (formatting/processing actions do not work)

### Expected Behavior (Correct)

2.1 WHEN a tool page that calls `registerToolData()` inside `{% block tool_js %}` is loaded THEN the system SHALL execute `registerToolData()` without error because `tool-runtime.js` is available before any tool script runs

2.2 WHEN the xml-formatter page is loaded THEN the system SHALL not throw any `SyntaxError` for `indentSize` because each variable is declared exactly once in its scope

2.3 WHEN the sql-beautifier page is loaded THEN the system SHALL not throw any `SyntaxError` for `BREAK_BEFORE` because each variable is declared exactly once in its scope

2.4 WHEN a tool page loads without JavaScript errors THEN the system SHALL allow the user to use the tool's formatting/processing functionality normally

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a tool page that does not call `registerToolData()` is loaded THEN the system SHALL CONTINUE TO load and function without errors

3.2 WHEN `registerToolData()` is called with a valid tool name and data object THEN the system SHALL CONTINUE TO register the data in `window.LamGenTools` as before

3.3 WHEN `getToolData()` is called after `registerToolData()` THEN the system SHALL CONTINUE TO return the registered tool data correctly

3.4 WHEN the xml-formatter page is loaded and `indentSize` is set via `setIndent()` THEN the system SHALL CONTINUE TO apply the correct indentation to formatted XML output

3.5 WHEN the sql-beautifier page is loaded and SQL is formatted THEN the system SHALL CONTINUE TO break SQL keywords onto new lines using the `BREAK_BEFORE` set as before

3.6 WHEN the json-formatter page is loaded THEN the system SHALL CONTINUE TO format, validate, and display JSON output correctly after the fix
