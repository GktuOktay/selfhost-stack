<?php
/*
 * Render harness for the selfhost/ partials with stubbed BookStack helpers (test tool only).
 * Runs in the pinned image (--network none): php render.php <theme-dir> <scenarios.json>
 * Blade is compiled by the image's own compiler; user(), userCan(), url() and env() are namespaced stubs,
 * collect() and e() are the real Laravel helpers. This is NOT the e2e test (that needs BookStack running).
 */
namespace T3Render {
    class Env { public static array $vars = []; public static bool $guest = false; public static bool $manage = false; public static string $theme = ''; }
    class UserStub { public function isGuest(): bool { return Env::$guest; } }
    function user() { return new UserStub(); }
    function userCan($p) { return $p === 'settings-manage' && Env::$manage; }
    function url($p) { return 'http://localhost:8701' . $p; }
    function env($k) { return Env::$vars[$k] ?? null; }

    class Book { public function __construct(public $id, public $name, public $updated_at) {} public function getUrl() { return '/books/' . $this->id; } }
    class Tag { public function __construct(public $id, public $name, public $value) {} }
    class Shelf { public $tags; public function __construct(array $tags) { $this->tags = collect($tags); } }

    class ViewEnv {
        private array $loops = [];
        public function make(string $name, array $data) { return new Rendered($name, $data); }
        public function addLoop($data): void { $n = is_countable($data) ? count($data) : 0; $this->loops[] = (object) ['index' => 0, 'count' => $n, 'first' => true]; }
        public function incrementLoopIndices(): void { $l = end($this->loops); $l->index++; }
        public function getLastLoop() { return end($this->loops) ?: null; }
        public function popLoop(): void { array_pop($this->loops); }
    }
    class Rendered {
        public function __construct(private string $name, private array $data) {}
        public function render(): string { return render_view($this->name, $this->data); }
    }

    function render_view(string $name, array $data): string {
        $rel = str_replace('.', '/', $name) . '.blade.php';
        $path = Env::$theme . '/' . $rel;
        if (!is_file($path)) { throw new \RuntimeException("no view $name"); }
        $compiler = new \Illuminate\View\Compilers\BladeCompiler(new \Illuminate\Filesystem\Filesystem(), '/tmp');
        $php = $compiler->compileString(file_get_contents($path));
        $fn = function (array $__data) use ($php) {
            $__env = new ViewEnv();
            extract($__data, EXTR_SKIP);
            ob_start();
            try { eval('namespace T3Render; ?>' . $php); } finally { $out = ob_get_clean(); }
            return $out;
        };
        return $fn($data);
    }

    function run(string $theme, array $scenarios): array {
        require_once '/app/www/vendor/autoload.php';
        Env::$theme = $theme;
        $out = [];
        foreach ($scenarios as $name => $sc) {
            Env::$vars = $sc['env'] ?? [];
            Env::$guest = $sc['guest'] ?? false;
            Env::$manage = $sc['manage'] ?? false;
            $tags = array_map(fn($t) => new Tag($t[0], $t[1], $t[2]), $sc['tags'] ?? []);
            $books = array_map(fn($b) => new Book($b[0], $b[1], $b[2]), $sc['books'] ?? []);
            try {
                $out[$name] = render_view($sc['view'], ['shelf' => new Shelf($tags), 'sortedVisibleShelfBooks' => $books]);
            } catch (\Throwable $e) {
                $out[$name] = 'EXCEPTION ' . get_class($e) . ': ' . $e->getMessage();
            }
        }
        return $out;
    }
}
namespace {
    error_reporting(E_ALL);
    set_error_handler(function ($no, $str, $file, $line) { throw new ErrorException($str, 0, $no, $file, $line); });
    $sc = json_decode(file_get_contents($argv[2]), true);
    echo json_encode(\T3Render\run($argv[1], $sc), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n";
}
