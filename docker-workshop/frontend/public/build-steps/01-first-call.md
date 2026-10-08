---
title: Make your first model call
editorFile: first_call.py
---

**7 minutes.** We will start by asking a model to write FizzBuzz. Before connecting the code, let's separate three things that are easy to mix up.

## The model, the API and the SDK

An **LLM**, or **large language model**, is trained on large amounts of text, including code, to generate responses to input. That training gives it patterns and knowledge it can use to answer questions, explain code and suggest changes. Its responses can vary, and useful-looking code still needs checking.

We will use an **OpenAI GPT model**. The starter selects `gpt-5`; your instructor may have configured another model through `AGENT_MODEL`.

| Part | Its job in this exercise |
| --- | --- |
| Model | Generates an assistant response from the messages we send. |
| API | The remote service interface our program calls to request that response. |
| Python SDK | OpenAI's Python library, which handles the HTTP request and gives us a Python response object. |

![Your Python program uses the OpenAI SDK to send messages through the OpenAI API to a GPT model, then receives an assistant response.](/images/model-call.svg)

Your instructor provides the API access for this workshop: the **key** authorizes requests, and the **endpoint** is the service address. The supplied client reads those values from its environment configuration. You do not need to edit `.env` for this exercise.

We use text messages here, although models can support other input and output types. Sending a request uses the trained model; it does not retrain its weights.

## Connect the request

Open **first_call.py** in Code. The supplied `FIZZBUZZ_PROMPT` asks for a Python function that returns FizzBuzz for 1–15. The program already creates an SDK client and will print the answer. You will complete the small `ask(client, prompt)` function between those steps.

1. Put `prompt` in a user message: `{"role": "user", "content": prompt}`.
2. Send that message list with `client.chat.completions.create`, passing `MODEL` and `messages`.
3. Return `response.choices[0].message.content`, or an empty string if content is absent.

`user` identifies the person's input; the response is an `assistant` message. `choices[0]` selects the first returned choice, and `.content` holds its text.

<details>
<summary>Hint</summary>

The SDK accepts named arguments `model=MODEL` and `messages=messages`. Returning the answer lets the caller decide what to do with it.

</details>

<details>
<summary>Copyable solution — replace the whole ask function</summary>

```python
def ask(client: Any, prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content or ""
```

</details>

## Run your first call

Save with **Ctrl/Cmd+S**, then select **Run code** below. The command runs in the visible **Terminal**. It uses the FizzBuzz prompt in your source file; you do not need to type it again.

```bash
uv run python first_call.py
```

Read the response. You should receive Python code, then return to the shell. Does its order of checks handle multiples of both 3 and 5? The program has printed generated code; it has not executed that code.

You now have one model call. An **agent** adds a **harness**: the program that supplies context, executes tools and decides when to ask the model again. We will build those capabilities one at a time.

For an API error, show the error to your instructor. Once the call works, try explaining where the response came from:

**Quick question:** which part generated the FizzBuzz code, and which part displayed it?

<details>
<summary>Compare your answer</summary>

The GPT model generated the response. The API returned it, the SDK exposed it as a Python object, and our Python program printed its text. The generated FizzBuzz function still has not run.

</details>

Can your program now handle **“Now change it to stop at 20”**? Keep your prediction in mind. After a short design discussion, we will try that exact follow-up and inspect what the program sends.

Optional reading: [OpenAI Chat Completions](https://developers.openai.com/api/reference/chat-completions/overview).
