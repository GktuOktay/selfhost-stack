{{-- Shelf header block (spec 0002 section 6.6, REQ-D15, CB-10, CB-11). Texts: U-21..U-23, U-28.
     Rule: the first tag named exactly plane-project (id order) decides; value trim, ASCII uppercase, ^[A-Z0-9]{1,12}$. --}}
@if($shelf->tags->sortBy('id')->where('name', 'plane-project')->count() > 0)
    @if(preg_match('#^[A-Z0-9]{1,12}$#D', strtoupper(trim($shelf->tags->sortBy('id')->where('name', 'plane-project')->first()->value))) === 1)
        <div class="mb-m" data-selfhost-shelf>
            <h2 class="mb-s">Proje: {{ strtoupper(trim($shelf->tags->sortBy('id')->where('name', 'plane-project')->first()->value)) }}</h2>
            <h3 class="text-muted mb-xs">Son güncellenen kitaplar</h3>
            @if(collect($sortedVisibleShelfBooks)->isEmpty())
                <p class="text-muted">Bu rafta görebileceğiniz kitap yok.</p>
            @else
                <ul class="mb-m">
                    @foreach(collect($sortedVisibleShelfBooks)->sortBy([['updated_at', 'desc'], ['id', 'desc']])->take(5) as $book)
                        <li><a href="{{ $book->getUrl() }}">{{ $book->name }}</a> <span class="text-muted">{{ $book->updated_at }}</span></li>
                    @endforeach
                </ul>
            @endif
        </div>
    @else
        <div class="mb-m text-muted" data-selfhost-notice>Proje etiketi geçersiz: {{ $shelf->tags->sortBy('id')->where('name', 'plane-project')->first()->value }}</div>
    @endif
    @if($shelf->tags->sortBy('id')->where('name', 'plane-project')->count() > 1)
        <div class="mb-m text-muted" data-selfhost-notice>Birden fazla proje etiketi var, ilki kullanıldı.</div>
    @endif
@endif
