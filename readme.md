# Dev Box

This addon contains some features that are primarily useful for software developers, but may also be useful for other users who work with text.

## Features
### Space folding
Let's look at this line from the ls utility manual.

<pre>
--sort=WORD            sort by WORD instead of name: none (-U), size (-S),
</pre>

You can see that there are 12 spaces in the middle, and nvda will skip them when reading the line as usual, but what if we want to read the line character by character?

Pressing nvda+up or nvda+numpad8 twice will read all the spaces one by one, which is usually not very convenient.

This addon detects 2 or more consecutive spaces, and folds them into a short sequence.
For example "space space space space space" becomes "5 space".

### Diff indication
When navigating through an object using numpad7 or numpad9, the addon checks for a diff character at the beginning of the line.

The space is ignored,  for the plus or minus a sound is played, to make addition/deletion easy to identify.

The sounds are taken from vscode, they are also slightly modified (a small amount of silence at the beginning and end is cut off).

### Line length checking
This feature allows to find out the length of the line under cursor, it can be useful when formatting code or any other text.
Gesture is unassigned by default.

---
All passive features, like space folding, is disabled by default, they could be enabled in addon settings.
