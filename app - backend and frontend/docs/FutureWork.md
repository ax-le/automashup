# Future Work

## For the Actual Code

- **Optimize the repitch function**: If possible, optimize this function as it makes the mashup outcome take a lot of time to process.
- **Avoid app reset on segment selection**: Prevent the app from resetting when selecting a segment on the segment preview. Although you can still interact with the app while it reloads, it is quite annoying.
- **Correct the segment summary's main track**: The main track in the segment summary is currently set to the Feed whose name is 'Track-1' instead of 'Input 1 (Beat structure)', as it should be. The challenge is to get the chosen input and set it as a global variable so it can be retrieved in the segment summary.
- **Quality of Life (QoL) improvement**: When saving a schema, sometimes the saving menu relaunches even though it does save the schema. It would be beneficial to check if it’s possible avoid this relaunch after saving.
- **Fix the delete button for track**: On the last tests, saw that delete track is not working properly.

## Propositions

- **Handle silence in missing segments**: Whenever there is silence due to a missing segment for any phase_fit method, either add another segment or use AI to generate a sound.
- **Make the segment summary interactive**: After the mashup with phase fit is created, make the segment summary interactive, allowing users to switch, remove, or add segments in a Lego-like interface.
- **Make the app suitable for mobile devices**: Enhance the app's usability on mobile devices.
- **Add a dark mode toggle**: Provide a dark mode option for better accessibility and user experience.

## Want to know the last advancements?

Download [this file](./documents/Changes%20since%20first%20version.docx){:download="awesome-file"} to check advancements from 17/06/24 until 09/08/24
