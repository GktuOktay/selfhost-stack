@if($shelf->tags->sortBy('id')->where('name', 'plane-project')->count() > 0)
  {{ $shelf->tags->sortBy('id')->where('name', 'plane-project')->first()->value }}
@endif
@if($shelf->tags->sortBy('id')->where('name', 'plane-project')->first())
x
@endif
