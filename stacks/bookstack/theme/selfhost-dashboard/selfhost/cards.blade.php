{{-- Application cards (spec 0002 REQ-D3, CB-2, CB-4). Texts: U-18, U-19, U-27. --}}
<div class="grid third gap-x-xxl no-row-gap mb-m">
    <div class="card content-wrap" data-selfhost-card="bookstack">
        <h3 class="mb-xs"><a href="{{ url('/books') }}">BookStack</a></h3>
        <p class="text-muted mb-none">Dokümantasyon</p>
    </div>

    <div class="card content-wrap" data-selfhost-card="penpot">
        @if(env('SELFHOST_PENPOT_STATE') === 'ok')
            @if(env('SELFHOST_PENPOT_URL') !== null && preg_match('#^https?://#i', env('SELFHOST_PENPOT_URL')) === 1)
                <h3 class="mb-xs"><a href="{{ env('SELFHOST_PENPOT_URL') }}" rel="noopener noreferrer">Penpot</a></h3>
                <p class="text-muted mb-none">Tasarım</p>
            @else
                <h3 class="mb-xs">Penpot</h3>
                <p class="text-muted mb-none">adres geçersiz</p>
            @endif
        @elseif(env('SELFHOST_PENPOT_STATE') === 'disabled')
            <h3 class="mb-xs">Penpot</h3>
            <p class="text-muted mb-none">Bu makinede etkin değil</p>
        @else
            <h3 class="mb-xs">Penpot</h3>
            <p class="text-muted mb-none">adres hesaplanamadı</p>
        @endif
    </div>

    <div class="card content-wrap" data-selfhost-card="plane">
        @if(env('SELFHOST_PLANE_STATE') === 'ok')
            @if(env('SELFHOST_PLANE_URL') !== null && preg_match('#^https?://#i', env('SELFHOST_PLANE_URL')) === 1)
                <h3 class="mb-xs"><a href="{{ env('SELFHOST_PLANE_URL') }}" rel="noopener noreferrer">Plane</a></h3>
                <p class="text-muted mb-none">Proje yönetimi</p>
            @else
                <h3 class="mb-xs">Plane</h3>
                <p class="text-muted mb-none">adres geçersiz</p>
            @endif
        @elseif(env('SELFHOST_PLANE_STATE') === 'disabled')
            <h3 class="mb-xs">Plane</h3>
            <p class="text-muted mb-none">Bu makinede etkin değil</p>
        @else
            <h3 class="mb-xs">Plane</h3>
            <p class="text-muted mb-none">adres hesaplanamadı</p>
        @endif
    </div>
</div>
