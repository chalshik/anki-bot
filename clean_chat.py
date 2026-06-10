import re

SRC = "WhatsApp Chat - goyim/_chat.txt"
DST = "WhatsApp Chat - goyim/_chat_clean.txt"

INVISIBLE = "‎‏"

HEADER_RE = re.compile(
    r"^[" + INVISIBLE + r"]?\[(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}:\d{2})\] ([^:]+): (.*)$"
)

MEDIA_OMITTED_RE = re.compile(
    r"\s*[" + INVISIBLE + r"]?(image|video note|video|sticker|GIF|audio|document) omitted\s*"
)

EDITED_TAG_RE = re.compile(r"\s*[" + INVISIBLE + r"]?<This message was edited>\s*$")
SYSTEM_CONTENT_RE = re.compile(
    r"created this group$|added (you|[^\n]+)$|Only messages that mention or people share with"
)


def strip_invisible(s):
    return s.strip(INVISIBLE).strip()


with open(SRC, encoding="utf-8") as f:
    raw_lines = f.read().splitlines()

messages = []
for line in raw_lines:
    m = HEADER_RE.match(line)
    if m:
        timestamp, sender, content = m.groups()
        messages.append([timestamp, strip_invisible(sender), content])
    else:
        if messages and line.strip():
            messages[-1][2] += "\n" + line

out_lines = []
for timestamp, sender, content in messages:
    content = strip_invisible(content)

    if sender == "goyim":
        continue
    if SYSTEM_CONTENT_RE.search(content):
        continue
    if content == "This message was deleted.":
        continue

    content = EDITED_TAG_RE.sub("", content)
    content = MEDIA_OMITTED_RE.sub("", content).strip()
    content = strip_invisible(content)
    if not content:
        continue

    out_lines.append(f"[{timestamp}] {sender}: {content}")

with open(DST, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines) + "\n")

print(f"Wrote {len(out_lines)} messages (from {len(messages)} total) to {DST}")
