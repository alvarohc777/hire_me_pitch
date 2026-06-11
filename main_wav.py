import asyncio

from dotenv import load_dotenv
from google import genai
from google.genai import types

import utils.audio_utils as au

load_dotenv()
client = genai.Client()


def read_text_file(path: str) -> str:
    """Safely reads a text file using UTF-8 encoding to prevent resource leaks

    and cross-platform character encoding crashes.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_user_prompt(config):
    job_description = config.get("job_description")
    resume = config.get("resume")
    user_prompt = config.get("user_prompt")
    return types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=f"=== JOB DESCRIPTION ===\n{job_description}"),
            types.Part.from_text(text=f"=== RESUME TO ANALYZE ===\n{resume}"),
            types.Part.from_text(text=f"{user_prompt}"),
        ],
    )


async def main():
    model_name = "gemini-3.1-flash-live-preview"

    # 2. Read instructions and data cleanly
    user_prompt = read_text_file("inputs/user_prompt.txt")
    job_description = read_text_file("inputs/job_description.txt")
    resume = read_text_file("inputs/resume.txt")
    system_prompt = read_text_file("inputs/system_prompt.txt")
    prompt_config = {
        "user_prompt": user_prompt,
        "job_description": job_description,
        "resume": resume,
    }

    # 3. Setup Config: Inject the system prompt into its proper structural container
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=system_prompt)]
        ),
    )

    print(f"Connecting to {model_name}...")

    # Using 'with' context manager ensures the output file safely closes when the loop finishes
    with au.stream_pcm_to_wav_init("respuesta.wav") as wav_file:
        async with client.aio.live.connect(model=model_name, config=config) as session:
            print("Connected! Sending context data...")

            # 4. Pass data cleanly using explicit structural headers
            user_content = build_user_prompt(prompt_config)
            await session.send_client_content(
                turns=[user_content],
            )

            # 5. Listen to the streaming response
            async for response in session.receive():
                if response.server_content is not None:
                    model_turn = response.server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            if part.inline_data and part.inline_data.data:
                                # Stream the incoming binary chunks straight onto the disk
                                # audio_file.write(part.inline_data.data)
                                au.write_wav_chunk(wav_file, part.inline_data.data)

                                print(".", end="", flush=True)
                if response.server_content and response.server_content.turn_complete:
                    print(
                        "\n\nTurn complete. Audio saved to 'respuesta.pcm'. Closing session."
                    )
                    break


if __name__ == "__main__":
    asyncio.run(main())
    print("converting into WAV into MP3")
    au.wav_to_mp3("respuesta.wav", "respuesta.mp3")
