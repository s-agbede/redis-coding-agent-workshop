# Design the agent with PEAS

**5 minutes.** Our destination is an agent that repairs this bug: a task looks complete, but becomes incomplete again after a browser refresh. What would the agent need to investigate it, and how would we know its repair worked?

**PEAS** gives us four design questions:

| Part | Question |
| --- | --- |
| **Performance** | How will we know the task succeeded? |
| **Environment** | Where will the agent work? |
| **Actuators** | What actions can it take? |
| **Sensors** | What information can it receive? |

## Try a design

Take two minutes with the person beside you to propose one or two items for each PEAS category for this repair. Then compare your design with the example below.

Consider: does “the agent says it is fixed” establish success? Is a filename enough to understand a function? Which actions should need your approval?

<details>
<summary>One design for our coding agent</summary>

| Part | Our choice | What we will build or use |
| --- | --- | --- |
| Performance | A completed task stays complete after refresh; existing behavior still works. | A later read, a browser refresh and independent application checks. |
| Environment | The local Python task-board project and its running application. | Project files, terminal commands and an app preview. |
| Actuators | Edit code and run checks. | Supplied replacement and command tools; approval for commands. |
| Sensors | Read code and receive the results of actions. | File tools, error messages, command output and test results. |

A file reader is a sensor because it brings information into the conversation. An editor changes the environment, making it an actuator. Running a command acts on the environment and also supplies observations through its output; these categories describe roles rather than mutually exclusive tool types.

</details>

## Use the design to choose the next step

Our first program can generate text, but a useful coding agent also needs relevant context. We will first preserve the conversation, then give the model file contents through a tool. Later, edits and command execution will let it act, and an evaluator will check the result.

**Quick question:** if we add a file editor but provide no way to read the project or run checks, which parts of this design are weak?

<details>
<summary>Compare your answer</summary>

It has an actuator but weak sensors and no trustworthy performance measurement. It can make a change without enough information to choose or assess it.

</details>

Keep these four questions in mind as the capabilities grow. Next, let's test our prediction about the FizzBuzz follow-up.

Further reading: [Designing AI agents from the outside in](https://samuelagbede.com/posts/designing-ai-agents-from-the-outside-in/).
