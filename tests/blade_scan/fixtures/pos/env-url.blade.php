@if(env('SELFHOST_PENPOT_STATE') === 'ok' && env('SELFHOST_PENPOT_URL') !== null)
{{ env('SELFHOST_PENPOT_URL') }}
@elseif(env('SELFHOST_PLANE_STATE') === 'disabled')
{{ env('SELFHOST_PLANE_URL') }}
@else
x
@endif
