/* 
 * Common replacement for console.log().
 * Use it anywhere you need logs, in form of _l() instead of console.log(),
 * It will be disabled in production.
 */
if (typeof JS_DEBUG != 'undefined' && JS_DEBUG) {
    var _l = function(){ console.log.apply(console, arguments); }
} else {
    var _l = function(){}
}
