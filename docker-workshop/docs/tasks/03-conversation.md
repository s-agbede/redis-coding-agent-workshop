# Keep the conversation

**9 minutes.** You have a FizzBuzz answer in the Terminal. Let's try continuing that conversation. Before running the command, predict: **will this request contain the earlier FizzBuzz code?**

## Try a follow-up

Select **Run code**. The supplied `--show-messages` option prints the message count, roles and content previews just before the SDK call:

```bash
uv run python first_call.py --show-messages --prompt "Now change it to stop at 20."
```

Find the request preview in Terminal. How many messages are there? Can you find either the original FizzBuzz request or the model's earlier code?

The preview contains one user message: the new instruction. Now look at `ask`: it builds that list afresh for each call. A model might ask for clarification or guess the intended task. Even a good guess does not add the missing history to the request.

The trace shows the messages passed to the SDK, not the model's internal reasoning. Long content previews are explicitly shortened for display; the full messages still go into the request.

We need to preserve both sides of the exchange and include them in the next request:

```text
First request:    user asks for FizzBuzz
Follow-up:        user asks for FizzBuzz → assistant's code → user's new instruction
```

This chat-completions interface does not automatically add earlier calls. Keeping that list is our harness's responsibility.

## Keep the messages

Open **checkpoints/stage1_chat.py**. The supplied chat program creates a list and passes it into `chat_turn(client, messages, user)` for each turn. Complete that function:

1. Append the new user message.
2. Send the entire list to the model.
3. Append the returned assistant message.
4. Return its text for display.

Do not create a new list inside the function. Keeping the assistant's response matters too: it contains the code the next instruction refers to. The SDK accepts the returned message object in later requests.

<details>
<summary>Hint</summary>

Use `messages.append(...)` before and after the SDK call. The caller keeps this same list between turns.

</details>

<details>
<summary>Copyable solution — replace the whole chat_turn function</summary>

```python
def chat_turn(client: Any, messages: list[Any], user: str) -> str:
    messages.append({"role": "user", "content": user})
    response = client.chat.completions.create(model=MODEL, messages=messages)
    message = response.choices[0].message
    messages.append(message)
    return message.content or ""
```

</details>

## Try the same exchange with history

Save, then select **Run code**:

```bash
uv run python -m checkpoints.stage1_chat --show-messages
```

Use **Copy text** and paste these prompts into the running chat one at a time:

```text
Write a Python function that returns FizzBuzz for the integers 1 to 15.
```

Before sending the next prompt, predict the roles you will see in its request preview:

```text
Now change it to stop at 20.
```

Compare your prediction with the actual messages. You should now see:

```text
user → assistant → user
```

Find the earlier code inside the assistant message. Compare the new answer with that code. Your two `append` calls let the next request carry both sides of the exchange; displaying an answer alone would not retain it.

If you restart after an edit, repeat both prompts: the new process begins with an empty history.

**Quick question:** have we taught the model this conversation permanently?

<details>
<summary>Compare your answer</summary>

No. The harness stores the messages and sends them with the next request. The model's trained weights are unchanged. Restarting this program discards the list; printing a reply does not automatically preserve it for a later call.

</details>

Keep the chat running for the next lesson. We have retained the conversation; next we need information from a local file.
