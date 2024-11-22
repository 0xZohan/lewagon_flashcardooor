# Le Wagon Flashcard Automation 🎴

Automatically complete Le Wagon bootcamp flashcards using Claude AI. This tool navigates through each module's flashcards, provides intelligent answers using Claude 3, and tracks progress automatically.

## Overview 🔍

This automation tool:
- Navigates through all Le Wagon bootcamp modules
- Identifies and processes flashcard sections
- Uses Claude AI to generate responses
- Handles both completed and incomplete card sets
- Provides detailed progress tracking
- Manages edge cases and state transitions

## Prerequisites 📋

- Python 3.10+
- Chrome browser
- Anthropic API key (Claude 3)
- Le Wagon bootcamp account

## Installation 🛠️

1. Clone the repository:
```bash
git clone https://github.com/0xZohan/lewagon_flashcardooor.git
cd lewagon-flashcard-automation
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
CLAUDE_API_KEY=your_claude_api_key_here
HOMEPAGE_URL=https://kitt.lewagon.com/camps/your_camp_id/challenges?path=your_path_here
```
*To note, your homepage URL should be the URL of the first challenge in your bootcamp. I.e. when you login to your Le Wagon account, and click 'Challenges', the URL in your browser will be the one you want to use.

## Requirements.txt 📄
```
selenium
python-dotenv
anthropic
requests
```

## Usage 🚀

1. Start the automation:
```bash
python flashcardooor.py
```

2. When prompted, log in to your Le Wagon account manually

3. Press Enter after logging in to start the automation

The script will:
- Navigate through all modules
- Expand each section with flashcards
- Process any unfinished flashcards
- Track and display progress
- Move to the next section automatically

## How It Works 🔧

1. **Module Navigation**: 
   - Identifies all available modules
   - Expands subcategories
   - Locates flashcard sections

2. **Flashcard Processing**:
   - Detects card state (flipped/unflipped)
   - Retrieves questions
   - Gets AI-generated answers from Claude
   - Handles card transitions
   - Tracks completion

3. **Progress Tracking**:
   - Shows overall progress
   - Identifies completed sections
   - Provides detailed logging
   - Handles various completion states

## States and Messages 📊

The script handles various flashcard states:
- "You still need to master all X cards"
- "You have mastered X out of Y cards"
- "You have mastered all X cards"

## Error Handling 🛟

The script includes:
- Retry logic for failed operations
- Screenshot capture on errors
- Detailed error logging
- State recovery mechanisms
- Edge case handling

## Debugging 🐛

If you encounter issues:
1. Check the console output for error messages
2. Look for screenshot captures in the project directory
3. Verify your API key and authentication
4. Ensure Chrome is up to date

## Contributing 🤝

1. Fork the repository
2. Create your feature branch
2. Make your changes
3. Submit a pull request

## Known Limitations ⚠️

- Requires manual login
- Chrome browser only
- Needs Claude API access

## File Structure 📁
```
lewagon-flashcard-automation/
├── flashcardooor.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Environment Setup Example 🔑
```bash
# .env file
CLAUDE_API_KEY=sk-ant-api...  # Your Claude API key
HOMEPAGE_URL=https://kitt.lewagon.com/camps/your_camp_id/challenges?path=your_path_here
```

## .gitignore Example 📝
```
.env
__pycache__/
*.pyc
*.png
error-*.html
page-source-*.html
```

## License 📜

MIT License - feel free to modify and distribute!

## Acknowledgments 🙏

- Le Wagon for their excellent bootcamp

## Support 💪

Create an issue in the repository for:
- Bug reports
- Feature requests
- General questions

Remember to never share your API keys or credentials when creating issues!