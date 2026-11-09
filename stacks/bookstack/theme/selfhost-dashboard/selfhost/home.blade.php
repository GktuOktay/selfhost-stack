{{-- Faz 1 dashboard block, included above the user-arranged #home-default grid (spec 0002 section 6.1). --}}
@if(! user()->isGuest())
    <div class="container px-xl py-s" data-selfhost-dashboard>
        @include('selfhost.cards')
    </div>
@endif
