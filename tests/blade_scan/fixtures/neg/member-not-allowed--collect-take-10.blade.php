{{ collect($sortedVisibleShelfBooks)->sortBy([['updated_at','desc'],['id','desc']])->take(10) }}
