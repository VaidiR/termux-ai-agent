# Sample Test Files

Place `.opus` audio files here to test the agent.

## Creating Test Files

If you have WhatsApp voice messages, they are stored as `.opus` files on your device. You can also create test files using `ffmpeg`:

```bash
# Record a short test clip (5 seconds) from microphone
termux-microphone-record -l 5 -f test.m4a
ffmpeg -i test.m4a -c:a libopus test_audio.opus

# Convert any audio file to opus
ffmpeg -i input.mp3 -c:a libopus -b:a 24k samples/test_audio.opus

# Create a silent test file (for testing the pipeline)
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 3 -c:a libopus samples/silent.opus
```

## WhatsApp Audio Location

WhatsApp voice messages are typically stored at:
```
/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Voice Notes/
```

Copy them to this directory for processing:
```bash
cp /storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp\ Voice\ Notes/202*/*.opus samples/
```
