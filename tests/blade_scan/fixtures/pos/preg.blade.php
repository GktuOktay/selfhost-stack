@if(preg_match('#^[A-Z0-9]{1,12}$#D', strtoupper(trim($shelf->tags->sortBy('id')->where('name', 'plane-project')->first()->value))) === 1)
x
@endif
