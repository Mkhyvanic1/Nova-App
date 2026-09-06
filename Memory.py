import json
import os

MEMORY_FILE = "nova_memory.json"
MAX_FACTS = 15


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def save_fact(key, value):
    memory = load_memory()
    memory[key] = value
    memory = summarize(memory)
    save_memory(memory)


def summarize(memory):
    if len(memory) > MAX_FACTS:
        keys = list(memory.keys())
        keys_to_remove = keys[:-MAX_FACTS]
        for k in keys_to_remove:
            del memory[k]
    return memory
