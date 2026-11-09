@forelse(collect($sortedVisibleShelfBooks)->sortBy([['updated_at', 'desc'], ['id', 'desc']])->take(5) as $book)
{{ $book->name }}
@empty
none
@endforelse
