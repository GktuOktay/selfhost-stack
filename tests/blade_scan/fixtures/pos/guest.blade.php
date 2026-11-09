@if(! user()->isGuest())
<p>x</p>
@endif
@if(userCan('settings-manage'))
<p>y</p>
@endif
