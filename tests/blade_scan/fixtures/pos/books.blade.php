@if(collect($sortedVisibleShelfBooks)->isEmpty())
empty
@else
@foreach(collect($sortedVisibleShelfBooks)->sortBy([['updated_at', 'desc'], ['id', 'desc']])->take(5) as $book)
<a href="{{ $book->getUrl() }}">{{ $book->name }}</a> {{ $book->updated_at }}
@endforeach
@endif
