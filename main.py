import json
import os
import random
from pathlib import Path
from collections import deque

# Get location of "study lists" directory
SCRIPT_DIR = Path(__file__).parent
STUDY_LISTS_PATH = SCRIPT_DIR / "Sets"
STUDY_LISTS_PATH.mkdir(exist_ok=True)

INPUT_STRING = " > "
SPLIT_CHAR = ";"
LABELS = ["a", "b", "c", "d"]
LABEL_NUMBERS = ["1", "2", "3", "4"]

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def multiple_choice_question(
    question,
    correct_answer,
    all_definitions,
    items_count,
    in_progress_count,
    finished_count,
):
    other_defs = [d for d in all_definitions if d["definition"] != correct_answer]

    # Not enough wrong answers → fallback
    if len(other_defs) < 3:
        return open_ended_question(
            question,
            correct_answer,
            items_count,
            in_progress_count,
            finished_count,
        )
    correct_location = random.randint(0, 3)

    # Get 3 wrong answers from other items
    other_defs = [d for d in all_definitions if d["definition"] != correct_answer]
    wrong_answers = random.sample(other_defs, min(3, len(other_defs)))

    choices = wrong_answers.copy()
    choices.insert(correct_location, {"definition": correct_answer})

    clear_screen()
    loading_bar(items_count, in_progress_count, finished_count)

    print(f"\n {question}")
    for i in range(len(choices)):
        print(f"{LABELS[i]}) {choices[i]['definition']}")

    while True:
        answer = input(INPUT_STRING).strip().lower()
        if answer in LABELS[:4]:
            answer_index = LABELS.index(answer)
            return answer_index == correct_location
        if answer in LABEL_NUMBERS[:4]:
            answer_index = LABEL_NUMBERS.index(answer)
            return answer_index == correct_location
        print("Please enter a letter a-d or number 1-4")


def open_ended_question(
    question, correct_answer, items_count, in_progress_count, finished_count
):
    clear_screen()
    loading_bar(items_count, in_progress_count, finished_count)
    print(f"\n {question}")
    answer = input(INPUT_STRING)
    return answer.strip().lower() == correct_answer.strip().lower()


def list_sets():
    list_files = os.listdir(STUDY_LISTS_PATH)
    if not list_files:
        return [], 0

    for item in range(len(list_files)):
        print(f"[{item + 1}] {list_files[item].removesuffix('.json')}")
    return list_files, len(list_files)


def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            input("Set file is corrupted. Press ENTER...")
            return []


def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def loading_bar(total, in_progress, finished):

    if total <= 0:
        return

    in_progress_part = int(in_progress / total * loading_bar_length)
    finished_part = int(finished / total * loading_bar_length)
    total_part = max(0, loading_bar_length - in_progress_part - finished_part)

    print(f"[{finished_part * '█'}{in_progress_part * '▒'}{total_part * ' '}]")


def set_chooser():
    while True:
        clear_screen()
        print("Choose set (or 'c' to cancel):")
        files, files_len = list_sets()

        if files_len == 0:
            input("No sets! Create one first. Press ENTER...")
            return None, True, None

        chosen_set = input(INPUT_STRING).strip()

        if chosen_set.lower() in ("cancel", "c"):
            return None, True, None

        try:
            index = int(chosen_set) - 1
            if 0 <= index < files_len:
                return (
                    read_json(STUDY_LISTS_PATH / files[index]),
                    False,
                    files[index].removesuffix(".json"),
                )
            else:
                input("Number out of range! Press ENTER...")
        except ValueError:
            input("Input a number! Press ENTER...")


def study_set():
    set_list, cancelled, chosen_set = set_chooser()

    if cancelled:
        return

    if not set_list or len(set_list) < 4:
        input("Set must have at least 4 items! Press ENTER...")
        return

    # Build cards
    cards = [
        {"item": item["item"], "definition": item["definition"], "stage": 0}
        for item in set_list
    ]

    if shuffle_enabled:
        random.shuffle(cards)

    queue = deque(cards)

    items_count = len(cards)
    finished_count = 0
    in_progress_count = 0

    while queue:
        card = queue.popleft()
        stage = card["stage"]

        # Skip finished cards
        if stage == 4:
            continue

        # Stage 0: introduce card
        if stage == 0:
            if in_progress_count >= max_cards_in_progress:
                queue.append(card)
                continue

            clear_screen()
            loading_bar(items_count, in_progress_count, finished_count)
            print(f"\nItem: {card['item']}")
            print(f"\nDefinition: {card['definition']}")
            input("\nPress ENTER...")

            card["stage"] = 1
            in_progress_count += 1
            queue.append(card)

        # Stage 1: multiple choice
        elif stage == 1:
            correct = multiple_choice_question(
                card["item"],
                card["definition"],
                cards,
                items_count,
                in_progress_count,
                finished_count,
            )

            if correct:
                input("\nCorrect! Press ENTER...")
                card["stage"] = 2
            else:
                input(f"\nWrong... The answer is: {card['definition']}\nPress ENTER...")

            queue.append(card)

        # Stage 2 & 3: open-ended
        elif stage in (2, 3):
            correct = open_ended_question(
                card["item"],
                card["definition"],
                items_count,
                in_progress_count,
                finished_count,
            )

            if correct:
                input("\nCorrect! Press ENTER...")
                card["stage"] += 1

                if card["stage"] == 4:
                    finished_count += 1
                    in_progress_count = max(0, in_progress_count - 1)
                    continue
            else:
                input(f"\nWrong... The answer is: {card['definition']}\nPress ENTER...")

            queue.append(card)

    clear_screen()
    loading_bar(items_count, 0, finished_count)
    input(f"\nFinished studying '{chosen_set}'! Press ENTER...")


def remove_items(set_file, index_str):
    sets = read_json(set_file)
    parts = [x.strip() for x in index_str.split(",")]

    indices_to_remove = []

    for part in parts:
        if ":" in part:
            start_str, end_str = part.split(":")
            try:
                start = int(start_str) - 1
                end = int(end_str) - 1
                for i in range(start, end + 1):
                    if 0 <= i < len(sets):
                        indices_to_remove.append(i)
            except ValueError:
                input("Invalid range format. Press ENTER...")
                return False
        else:
            try:
                idx = int(part) - 1
                if 0 <= idx < len(sets):
                    indices_to_remove.append(idx)
            except ValueError:
                input("Invalid item number. Press ENTER...")
                return False

    # Remove in reverse order to maintain indices
    for idx in sorted(set(indices_to_remove), reverse=True):
        sets.pop(idx)

    write_json(set_file, sets)
    return True


def add_item(set_file, item_text, definition_text):
    sets = read_json(set_file)

    if not item_text.strip() or not definition_text.strip():
        return False

    sets.append({"item": item_text.strip(), "definition": definition_text.strip()})

    write_json(set_file, sets)
    return True


def edit_item(set_file, index, new_item, new_definition):
    sets = read_json(set_file)
    if 0 <= index < len(sets):
        if new_item:
            sets[index]["item"] = new_item
        if new_definition:
            sets[index]["definition"] = new_definition

        write_json(set_file, sets)
        return True

    input("Invalid item number. Press ENTER...")
    return False


def display_set(set_file):
    clear_screen()
    sets = read_json(set_file)

    if not sets:
        print("This set is empty!")
        return

    max_len_items = max(len(item["item"]) for item in sets) + 1
    print("Current items:\n")
    for idx, task in enumerate(sets, 1):
        print(f"[{idx}] {task['item'].ljust(max_len_items, ' ')}= {task['definition']}")
    print()


def edit_set():
    set_list, if_cancelled, chosen_set = set_chooser()

    if if_cancelled:
        return

    set_file = STUDY_LISTS_PATH / f"{chosen_set}.json"

    while True:
        display_set(set_file)

        print(
            "Commands: add/a [item];[definition], remove/rm [index], edit/e [index];[item];[definition], done/d"
        )
        choice = input(INPUT_STRING).strip()

        if not choice:
            continue

        # Split command from the rest
        parts = choice.split(maxsplit=1)
        command = parts[0].lower()

        if command in ("add", "a"):
            if len(parts) < 2:
                input("Invalid syntax: a [item];[definition]\nPress ENTER...")
                continue

            # Split the rest by semicolon
            data_parts = parts[1].split(";")
            if len(data_parts) != 2:
                input("Invalid syntax: a [item];[definition]\nPress ENTER...")
                continue

            item = data_parts[0].strip()
            definition = data_parts[1].strip()

            if add_item(set_file, item, definition):
                print("Added!")
            else:
                input("Failed to add. Press ENTER...")

        elif command in ("remove", "rm"):
            if len(parts) < 2:
                input("Invalid syntax: rm [index]\nPress ENTER...")
                continue

            index_str = parts[1].strip()
            if remove_items(set_file, index_str):
                print("Removed!")

        elif command in ("edit", "e"):
            if len(parts) < 2:
                input(
                    "Invalid syntax: e [index];[item];[definition]\nUse '-' to keep current value. Press ENTER..."
                )
                continue

            # Split the rest by semicolon
            data_parts = parts[1].split(";")
            if len(data_parts) != 3:
                input("Invalid syntax: e [index];[item];[definition]\nPress ENTER...")
                continue

            try:
                index = int(data_parts[0].strip()) - 1
                new_item = data_parts[1].strip()
                new_definition = data_parts[2].strip()

                new_item = "" if new_item == "-" else new_item
                new_definition = "" if new_definition == "-" else new_definition

                if new_item or new_definition:
                    if edit_item(set_file, index, new_item, new_definition):
                        print("Updated!")
                else:
                    print("No changes made.")
            except ValueError:
                input("Invalid number. Press ENTER...")

        elif command in ("done", "d"):
            return

        else:
            input("Unknown command. Press ENTER...")


def create_set():
    set_list = []

    clear_screen()
    create_or_import = input("Create (c) or Import (i)? ").strip().lower()

    if create_or_import in ("c", "create"):
        file_name = input("Set name: ").strip()
        if not file_name:
            input("Name required! Press ENTER...")
            return

        file_name = file_name + ".json"

        print("\nEnter items (type 'done' or 'd' when finished):")
        while True:
            added_item = input("\nItem (or 'done'): ").strip()
            if added_item.lower() in ("done", "d"):
                if len(set_list) < 4:
                    print("Need at least 4 items!")
                    continue
                write_json(STUDY_LISTS_PATH / file_name, set_list)
                input(f"Set '{file_name}' created! Press ENTER...")
                return
            if not added_item:
                continue

            added_definition = input(f"Definition for '{added_item}': ").strip()
            if added_definition:
                set_list.append({"item": added_item, "definition": added_definition})

    elif create_or_import in ("i", "import"):
        file_name = input("Set name: ").strip()
        if not file_name:
            input("Name required! Press ENTER...")
            return

        file_name = file_name + ".json"

        print(f"\nPaste text (format: item{SPLIT_CHAR}definition per line):")
        print("Type 'END' on a new line when done:\n")

        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)

        string_to_import = "\n".join(lines)

        for line in string_to_import.split("\n"):
            line = line.strip()
            if not line:
                continue

            if SPLIT_CHAR in line:
                parts = line.split(SPLIT_CHAR, 1)
                if len(parts) == 2:
                    item = parts[0].strip()
                    definition = parts[1].strip()
                    if item and definition:
                        set_list.append({"item": item, "definition": definition})

        if len(set_list) < 4:
            input(
                f"Only imported {len(set_list)} items. Need at least 4! Press ENTER..."
            )
            return

        write_json(STUDY_LISTS_PATH / file_name, set_list)
        input(f"Imported {len(set_list)} items into '{file_name}'! Press ENTER...")


def config():
    config_file = SCRIPT_DIR / "config.json"

    # Create default config if it doesn't exist
    if not config_file.exists():
        default_config = {"loading bar length": 30, "shuffle": True}
        write_json(config_file, default_config)
        return default_config["loading bar length"], default_config["shuffle"]

    settings = read_json(config_file)
    return (
        settings.get("loading_bar_length", 30),
        settings.get("shuffle", True),
        settings.get("max_cards_in_progress", 6),
    )


def main_menu():
    while True:
        clear_screen()
        print(
            r"""
   _____ __            __      _____                 __         _      __  
  / ___// /___  ______/ /_  __/ ___/____ _____  ____/ /      __(_)____/ /_ 
  \__ \/ __/ / / / __  / / / /\__ \/ __ `/ __ \/ __  / | /| / / / ___/ __ \
 ___/ / /_/ /_/ / /_/ / /_/ /___/ / /_/ / / / / /_/ /| |/ |/ / / /__/ / / /
/____/\__/\__,_/\__,_/\__, //____/\__,_/_/ /_/\__,_/ |__/|__/_/\___/_/ /_/ 
                     /____/                                                  

                            [1. Study      ]
                            [2. Edit       ]
                            [3. Create     ]
                            [4. Exit       ] 

"""
        )
        choice = input(INPUT_STRING).strip().lower()

        if choice in ("1", "study"):
            study_set()
        elif choice in ("2", "edit", "edit set"):
            edit_set()
        elif choice in ("3", "create", "create set"):
            create_set()
        elif choice in ("4", "exit"):
            if input("Are you sure you want to exit (y/N):").strip().lower() in ("y", "yes"):
                return
            continue
        else:
            input("Invalid choice! Press ENTER...")


if __name__ == "__main__":
    loading_bar_length, shuffle_enabled, max_cards_in_progress = config()
    main_menu()
