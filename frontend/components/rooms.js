// Shared room/subject metadata. Mirrors the subjects seeded in database/schema.sql
// so the room list still works even if the /api/chat/subjects call fails.
export const DEFAULT_ROOMS = [
  { name: 'Physics', description: 'Physics and physical sciences' },
  { name: 'Biology', description: 'Biology and life sciences' },
  { name: 'Calculus', description: 'Calculus and mathematical analysis' },
  { name: 'Chemistry', description: 'Chemistry and chemical sciences' },
  { name: 'Programming', description: 'Computer programming and software development' },
  { name: 'History', description: 'History and historical topics' },
  { name: 'Literature', description: 'Literature and language arts' },
  { name: 'General', description: 'General knowledge and miscellaneous topics' },
]

export const ROOM_STORAGE_KEY = 'studeymate.activeRoom'

export const VISIBLE_ROOM_COUNT = 3
