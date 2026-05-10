# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Script Ordering and Duplicate Declaration Bugs
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bugs exist
  - **Scoped PBT Approach**: For deterministic bugs, scope the property to the concrete failing cases
  - Test 1: Parse `templates/base.html` and assert `tool-runtime.js` script tag appears BEFORE `{% block extra_js %}` — will FAIL on unfixed code
  - Test 2: Parse `templates/tools/developer/xml-formatter.html` script block and assert `let indentSize` appears exactly once — will FAIL if duplicate exists
  - Test 3: Parse `templates/tools/developer/sql-beautifier.html` script block and assert `const BREAK_BEFORE` appears exactly once — will FAIL if duplicate exists
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Test 1 FAILS (proves script ordering bug exists); Tests 2 & 3 pass or fail depending on current state
  - Document counterexamples found to understand root cause
  - Mark task complete when tests are written, run, and results are documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Buggy Tool Pages and Runtime API Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: `registerToolData` and `getToolData` API contract on unfixed code
  - Observe: `xml-formatter` `setIndent` behavior on unfixed code
  - Observe: `sql-beautifier` `BREAK_BEFORE` set drives keyword line-breaking
  - Write property-based test: for all valid tool names and data objects, `registerToolData` then `getToolData` round-trips correctly
  - Write test: `base.html` renders `{% block tool_js %}` block (tools not using `registerToolData` are unaffected)
  - Write test: `xml-formatter` script block contains `setIndent` function definition
  - Write test: `sql-beautifier` script block contains `BREAK_BEFORE` set and `formatSql` function
  - Verify tests pass on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. Fix for tools-page-js-errors

  - [x] 3.1 Implement Fix 1 — move tool-runtime.js before {% block extra_js %} in base.html
    - In `templates/base.html`, move `<script src="{% static 'js/tool-runtime.js' %}">` to before `{% block extra_js %}{% endblock %}`
    - This ensures `window.registerToolData` and `window.getToolData` are defined before any inline script in `extra_js` or `tool_js` runs
    - _Bug_Condition: isBugCondition(pageLoad) where pageLoad.template extends tool_base.html AND calls registerToolData() AND tool-runtime.js not yet loaded_
    - _Expected_Behavior: tool-runtime.js loads before {% block extra_js %} so registerToolData is defined when tool scripts execute_
    - _Preservation: All tool pages not calling registerToolData are unaffected; tool-runtime.js API unchanged_
    - _Requirements: 2.1, 2.4, 3.1, 3.2, 3.3_

  - [x] 3.2 Implement Fix 2 — remove duplicate let indentSize in xml-formatter.html (if present)
    - In `templates/tools/developer/xml-formatter.html`, ensure `let indentSize = 2;` appears exactly once
    - Remove any duplicate declaration if found
    - _Bug_Condition: isBugCondition(pageLoad) where occurrences('let indentSize', scriptContent) > 1_
    - _Expected_Behavior: let indentSize declared exactly once; no SyntaxError on parse_
    - _Preservation: setIndent() continues to update indentSize and re-format output_
    - _Requirements: 2.2, 3.4_

  - [x] 3.3 Implement Fix 3 — remove duplicate const BREAK_BEFORE in sql-beautifier.html (if present)
    - In `templates/tools/developer/sql-beautifier.html`, ensure `const BREAK_BEFORE` appears exactly once
    - Remove any duplicate declaration if found
    - _Bug_Condition: isBugCondition(pageLoad) where occurrences('const BREAK_BEFORE', scriptContent) > 1_
    - _Expected_Behavior: const BREAK_BEFORE declared exactly once; no SyntaxError on parse_
    - _Preservation: formatSql() continues to use BREAK_BEFORE set for keyword line-breaking_
    - _Requirements: 2.3, 3.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Script Ordering and Duplicate Declaration Bugs Fixed
    - **IMPORTANT**: Re-run the SAME tests from task 1 - do NOT write new tests
    - The tests from task 1 encode the expected behavior
    - When these tests pass, they confirm the expected behavior is satisfied
    - Run bug condition exploration tests from step 1
    - **EXPECTED OUTCOME**: All tests PASS (confirms bugs are fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Buggy Tool Pages and Runtime API Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
