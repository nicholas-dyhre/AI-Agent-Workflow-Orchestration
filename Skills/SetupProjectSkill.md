# Project creation

The only way to create projects is to the creation tools:

- use `CreateFolderTool` to create folders. Not projects. Not runnable code. Not setup of frameworks.
- use `FileWriterTool` to create file and add content to it. Extremely useful for creating code and tests.
- use `PatchFileTool` to patch existing files. Not useful for creating projects, but can be used to patch existing files, if full override is not desired.
- use `ExecuteConsoleCommandTool` to execute console commands. Useful for creating projects using console commands.

Using all of these tools, gives the complete toolset to create projects, create code and tests.

The only way to verify projects is to the verification tools:
**IMPORTANT** Verification tools will only provide desired outcomes, if the tools are used after the creation tools.

- use `ListFilesTool` to list all files in the project directory. Ensure the files listed are as you expect.
- use `RunProjectTool` or run the project.
- use `RunTestsTool` to run the tests tests.
