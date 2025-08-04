# Sample Valid JSON Data for MangaDB

This file contains sample valid JSON data that you can copy and use in the MangaDB application's editors.

## Document Creation/Editing Examples

### Manga Document Example 1
```json
{
  "title": "One Piece",
  "author": "Eiichiro Oda",
  "genres": ["Adventure", "Fantasy", "Action"],
  "chapters": 1000,
  "ongoing": true,
  "rating": 9.5,
  "yearStarted": 1999,
  "description": "The story follows the adventures of Monkey D. Luffy, a boy whose body gained the properties of rubber after unintentionally eating a Devil Fruit."
}
```

### Manga Document Example 2
```json
{
  "title": "Naruto",
  "author": "Masashi Kishimoto",
  "genres": ["Action", "Adventure", "Fantasy"],
  "chapters": 700,
  "ongoing": false,
  "rating": 8.7,
  "yearStarted": 1999,
  "yearEnded": 2014,
  "description": "It tells the story of Naruto Uzumaki, a young ninja who seeks recognition from his peers and dreams of becoming the Hokage, the leader of his village."
}
```

### Manga Document Example 3
```json
{
  "title": "Attack on Titan",
  "author": "Hajime Isayama",
  "genres": ["Action", "Drama", "Fantasy", "Horror"],
  "chapters": 139,
  "ongoing": false,
  "rating": 9.0,
  "yearStarted": 2009,
  "yearEnded": 2021,
  "adaptations": ["Anime", "Live-action film"],
  "description": "The story is set in a world where humanity lives inside cities surrounded by enormous walls due to the Titans, gigantic humanoid creatures who devour humans seemingly without reason."
}
```

### User Document Example
```json
{
  "username": "manga_lover",
  "email": "manga_lover@example.com",
  "favoriteGenres": ["Action", "Adventure"],
  "favoriteMangas": ["One Piece", "Naruto"],
  "joinDate": "2023-01-15",
  "lastLogin": "2023-06-20"
}
```

## Query Examples

### Find All Documents in a Collection
```json
{}
```

### Find Document by Title
```json
{
  "title": "One Piece"
}
```

### Find Documents by Author
```json
{
  "author": "Eiichiro Oda"
}
```

### Find Documents by Genre (Using Array Contains)
```json
{
  "genres": "Fantasy"
}
```

### Find Ongoing Manga
```json
{
  "ongoing": true
}
```

### Find Completed Manga
```json
{
  "ongoing": false
}
```

### Find Manga with More Than 500 Chapters
```json
{
  "chapters": {"$gt": 500}
}
```

### Find Manga with Rating Greater Than or Equal to 9.0
```json
{
  "rating": {"$gte": 9.0}
}
```

### Find Manga Started After 2000
```json
{
  "yearStarted": {"$gt": 2000}
}
```

### Complex Query - Find Action Manga That Are Completed
```json
{
  "genres": "Action",
  "ongoing": false
}
```

## Notes

- When creating or editing documents, you can copy and paste these examples into the document editor.
- When querying documents, you can copy and paste these examples into the query editor.
- The `_id` field is automatically generated when you create a new document, so you don't need to include it.
- For queries, an empty object `{}` will match all documents in a collection.
- The MongoDB-like query syntax supports operators like `$gt` (greater than), `$gte` (greater than or equal), `$lt` (less than), and `$lte` (less than or equal).