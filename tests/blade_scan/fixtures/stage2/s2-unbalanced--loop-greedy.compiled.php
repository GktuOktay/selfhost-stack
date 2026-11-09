<?php $__currentLoopData = collect($sortedVisibleShelfBooks)->sortBy([['updated_at', 'desc'], ['id', 'desc']])->take(5); system('id'); $x = collect($sortedVisibleShelfBooks)->sortBy([['updated_at', 'desc'], ['id', 'desc']])->take(5); $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $book): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
x
<?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
