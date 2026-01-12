# StudySandwich

A simple terminal-based flashcard study app with spaced repetition.

## Usage

Run the program:
```bash
python study_sandwich.py
```

### Creating a Set

Choose **Create** from the menu, then either:
- **Create**: Manually add items one by one (minimum 4 items)
- **Import**: Paste text in format `item;definition` per line, then type `END`

### Studying

Choose **Study**, select your set, and work through the cards. Cards progress through 4 stages:
1. Introduction (see both sides)
2. Multiple choice
3. Open-ended question
4. Second open-ended (mastered after this)

Answer multiple choice with `a-d` or `1-4`. For open-ended, type the exact definition.

### Editing Sets

Choose **Edit** and use these commands:
- `add item;definition` - Add new item
- `rm 1` or `rm 1,3,5` or `rm 1:5` - Remove items
- `edit 1;new item;new definition` - Edit item (use `-` to keep current value)
- `done` - Exit

## Configuration

Edit `config.json` to customize:
- `shuffle`: Randomize cards (default: true)
- `max_cards_in_progress`: How many cards to learn at once (default: 6)
- `loading_bar_length`: Progress bar width (default: 30)

## File Structure

```
Sets/
  ├── your_set.json
  └── another_set.json
config.json
```
