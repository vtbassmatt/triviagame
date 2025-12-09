# macOS Emoji Picker in Firefox

## Issue

On macOS (Sonoma 14.x and later), pressing `Fn-e` or the 🌐 globe key may not bring up the emoji picker in Firefox when editing questions, answers, or other text fields. Instead, it may just type the letter "e".

## Root Cause

This is a **Firefox browser bug** that affected versions prior to Firefox 134. The bug was caused by Firefox improperly forwarding system keyboard shortcut events, causing the emoji picker to flash briefly and then disappear immediately.

## Solutions

### Best Solution: Update Firefox

Update to **Firefox 134 or newer** (released January 2025). This version includes the official fix for this issue.

To update Firefox:
1. Open Firefox
2. Click the menu button (☰)
3. Select "Help" → "About Firefox"
4. Firefox will automatically check for and install updates

### Alternative Solutions

If you cannot update Firefox immediately:

1. **Use the alternative keyboard shortcut**: Press `Ctrl+Cmd+Space` instead of `Fn-e`

2. **Use the Edit menu**: 
   - Click "Edit" in the menu bar
   - Select "Emoji & Symbols"

3. **Use a different browser**: The emoji picker works correctly in:
   - Safari
   - Chrome/Edge
   - Other Chromium-based browsers

### System-Level Troubleshooting

If the emoji picker doesn't work in any application:

1. **Check keyboard settings**:
   - Open System Settings → Keyboard
   - Ensure "Show Emoji & Symbols" is enabled
   - Check the Globe/🌐 key assignment

2. **Check for software interference**:
   - Some security software (antivirus, VPNs) may enable "Secure Keyboard Entry" which blocks the emoji picker
   - Password managers can also interfere
   - Try closing these apps temporarily

3. **Restart your Mac**: Sometimes the emoji picker process needs to be restarted

## Technical Details

The triviagame application uses standard HTML `<textarea>` elements without any JavaScript that interferes with keyboard events. The issue is entirely within the Firefox browser's handling of macOS system shortcuts.

## References

- [Firefox Bug Discussion](https://discourse.mozilla.org/t/macos-sonoma-emoji-shortcut-stopped-working-on-firefox-v119/123991)
- [Technical Explanation](https://chester.me/archives/2024/02/a-workaround-to-fix-the-firefox-emoji-keyboard-shortcut-on-macos-sonoma/)
