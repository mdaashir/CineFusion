# CineFusion 🎬

A modern movie search and recommendation web application with intelligent autocomplete functionality.

## Features

- **Movie Search**: Search through a comprehensive movie database
- **Smart Autocomplete**: Trie-based autocomplete for fast search suggestions
- **User Authentication**: Secure login and signup system
- **Search History**: Track and view previous searches
- **Responsive Design**: Works on desktop and mobile devices
- **Movie Metadata**: Access detailed movie information including ratings, cast, and genres

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python
- **Data Structures**: AVL Tree, Trie for optimized search
- **Database**: CSV-based movie metadata storage

## Project Structure

```
CineFusion/
├── Frontend/
│   ├── index.html          # Main entry point
│   ├── css/               # Stylesheets
│   ├── html/              # HTML pages
│   ├── js/                # JavaScript files
│   └── img/               # Images and assets
├── Backend/
│   └── process/           # Python processing scripts
│       ├── avl.py         # AVL tree implementation
│       ├── trie.py        # Trie-based autocomplete
│       └── movie_metadata.csv # Movie database
└── README.md
```

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/mdaashir/CineFusion.git
   cd CineFusion
   ```

2. Open `Frontend/index.html` in your web browser

3. For the Python backend features:
   ```bash
   cd Backend/process
   python trie.py
   ```

## Features in Development

- [ ] Backend API integration
- [ ] Real-time movie data fetching
- [ ] User preference learning
- [ ] Advanced filtering options
- [ ] Movie recommendations based on viewing history

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
