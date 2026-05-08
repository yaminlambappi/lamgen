/**
 * LamGen Tool Runtime Namespace
 * Safe global namespace for all tool-specific data and utilities
 * Prevents variable collisions between multiple tools
 */

window.LamGenTools = window.LamGenTools || {};

/**
 * Register tool data safely in the global namespace
 * @param {string} toolName - Unique tool identifier (e.g., 'yamlFormatter', 'jsonFormatter')
 * @param {object} data - Tool data object (examples, constants, etc.)
 */
window.registerToolData = function(toolName, data) {
    if (window.LamGenTools[toolName]) {
        console.warn(`Tool "${toolName}" is already registered. Overwriting...`);
    }
    window.LamGenTools[toolName] = data;
};

/**
 * Get tool data safely
 * @param {string} toolName - Tool identifier
 * @param {*} defaultValue - Default value if tool data not found
 */
window.getToolData = function(toolName, defaultValue) {
    return window.LamGenTools[toolName] || defaultValue;
};
