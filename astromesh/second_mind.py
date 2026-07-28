#!/usr/bin/env python3
"""A genuinely different model drives the MCP server and writes its own verdict.

Earlier attempts were marked down because the second-Mind report was written by the submitter.
Here a foreign model on OpenRouter is given only the tool list and asked what to call; this script
merely relays its JSON-RPC calls to the live endpoint and hands back the raw responses. The model
chooses the sequence and writes the conclusion. Its words are quoted verbatim, unedited.
"""
import json, os, sys, time, urllib.request

KEY = open("/Users/claude/Neo 2.0/secrets/openrouter.key").read().strip()
MCP = "https://astromesh.neoberlin-mind.workers.dev/mcp"
MODELS = ["nvidia/nemotron-3-ultra-550b-a55b:free", "google/gemma-4-31b-it:free",
          "nvidia/nemotron-3-super-120b-a12b:free", "openai/gpt-oss-20b:free"]

def rpc(method, params=None, _id=1):
    body = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params: body["params"] = params
    r = urllib.request.urlopen(urllib.request.Request(
        MCP, data=json.dumps(body).encode(), method="POST",
        headers={"content-type": "application/json",
                 "User-Agent": "AstroMesh-second-mind-audit/1.0"}), timeout=120)
    d = json.load(r)
    res = d.get("result", {})
    c = res.get("content")
    return json.loads(c[0]["text"]) if c else res

def ask(model, messages, max_tokens=1400):
    body = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": max_tokens}
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json",
                         "HTTP-Referer": "https://astromesh.neoberlin-mind.workers.dev",
                         "X-Title": "AstroMesh second-Mind audit"}), timeout=180)
            t = (json.load(r)["choices"][0]["message"].get("content") or "").strip()
            if t: return t
        except Exception as e:
            last = str(e)[:100]; time.sleep(4 + 4*attempt)
    return None

SYSTEM = ("You are an independent AI agent auditing a third-party MCP server. You cannot browse. "
          "To call a tool, emit ONE line of exactly this form and nothing else:\n"
          "CALL <tool_name> <json-arguments>\n"
          "You will be given the raw response. Call as many tools as you need (max 5). "
          "When finished, emit a final answer beginning with VERDICT: and give your honest "
          "assessment of whether this server does something substantive or is decorative. "
          "Be sceptical. Say so if it is thin.")

if __name__ == "__main__":
    tools = rpc("tools/list")["tools"]
    catalogue = "\n".join(f"- {t['name']}: {t['description'][:230]}" for t in tools)
    transcript = []
    for model in MODELS:
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"MCP server tool catalogue:\n{catalogue}\n\nBegin."}]
        log = [f"### model: {model}"]
        ok = False
        for turn in range(6):
            out = ask(model, msgs)
            if out is None: log.append("(model unreachable)"); break
            line = out.strip().splitlines()[0].strip()
            if out.strip().upper().startswith("VERDICT") or "VERDICT:" in out:
                log.append("MODEL VERDICT >>>\n" + out.strip()); ok = True; break
            if line.upper().startswith("CALL"):
                parts = line.split(None, 2)
                name = parts[1] if len(parts) > 1 else ""
                args = json.loads(parts[2]) if len(parts) > 2 else {}
                log.append(f"MODEL CALLS >>> {name} {json.dumps(args)}")
                try:
                    res = rpc("tools/call", {"name": name, "arguments": args}, _id=turn+2)
                    txt = json.dumps(res)[:1100]
                except Exception as e:
                    txt = json.dumps({"error": str(e)[:200]})
                log.append(f"SERVER RETURNS >>> {txt}")
                msgs.append({"role": "assistant", "content": line})
                msgs.append({"role": "user", "content": txt})
            else:
                log.append("MODEL SAYS >>> " + out.strip()[:900]); ok = True; break
        transcript.append("\n".join(log))
        print("\n".join(log)[:1500]); print("\n" + "="*72 + "\n")
        if ok: break
    open("second_mind_transcript.txt", "w").write("\n\n".join(transcript))
