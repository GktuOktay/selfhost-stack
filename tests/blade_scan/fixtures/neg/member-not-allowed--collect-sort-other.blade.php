{{ collect($sortedVisibleShelfBooks)->sortBy('name')->take(5) }}
