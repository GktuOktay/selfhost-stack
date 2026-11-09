<?php
/*
 * Spec 0002 section 6.1: two-stage Blade/PHP scanner for the theme partials (selfhost/*.blade.php).
 *
 * Runs inside the pinned BookStack image (php + Laravel's Blade compiler), --network none:
 *   php scan.php <allowlist-dir> <path>...
 * <allowlist-dir> holds PHP_ALLOWLIST and ACCESS_ALLOWLIST. Each <path> is a file or a directory
 * (searched recursively): *.blade.php gets stage 1 (Blade source) and stage 2 (compiled output),
 * *.compiled.php gets stage 2 only (hand-written negative fixtures for the compiler stage).
 *
 * Output: one JSON object {"results": {file: [{stage, rule, detail}]}, "config_error": null|string}.
 * Exit code is always 0 when the JSON was produced; the caller decides what a violation means.
 * Nothing here is "best effort": anything not explicitly allowed is a violation (fail closed).
 */

error_reporting(E_ALL);

final class Cfg
{
    /** @var array<string,true> lower-case function names */
    public array $functions = [];
    /** @var array<string,string> normalized expression => entry id */
    public array $access = [];
    /** @var array<string,array<string,string>> alias(without $) => [normalized source => id] */
    public array $foreach = [];
    /** @var array<string,true> lower-case function names that appear as bare calls in ACCESS (restricted) */
    public array $restrictedCalls = [];

    public const BASE_VARS = ['shelf', 'sortedVisibleShelfBooks', 'loop'];
    public const ENV_NAMES = ['SELFHOST_PENPOT_URL', 'SELFHOST_PLANE_URL', 'SELFHOST_PENPOT_STATE', 'SELFHOST_PLANE_STATE'];
    public const DIRECTIVES_WITH_ARGS = ['if', 'elseif', 'isset', 'foreach', 'forelse', 'include'];
    public const DIRECTIVES_NO_ARGS = ['else', 'endif', 'endforeach', 'empty', 'endforelse', 'endisset'];
    public const FORBIDDEN_CALLS = [
        'config', 'app', 'resolve', 'call_user_func', 'call_user_func_array', 'exec', 'shell_exec', 'system',
        'passthru', 'proc_open', 'popen', 'eval', 'readfile', 'request', 'curl_init', 'curl_exec', 'curl_setopt',
        'fsockopen', 'stream_socket_client', 'stream_socket_server', 'file_put_contents', 'unlink',
        'file_get_contents', 'fopen', 'file',
    ];
    public const FORBIDDEN_NAMES = ['storage', 'file', 'db', 'http', 'html', 'htmlstring', 'splfileobject', 'process'];

    public static function load(string $dir): self
    {
        $c = new self();
        $f = $dir . '/PHP_ALLOWLIST';
        if (!is_file($f)) {
            throw new RuntimeException("missing $f");
        }
        foreach (file($f, FILE_IGNORE_NEW_LINES) as $n => $line) {
            $t = trim($line);
            if ($t === '' || $t[0] === '#') {
                continue;
            }
            if (!preg_match('/^[A-Za-z_][A-Za-z0-9_]*$/', $t)) {
                throw new RuntimeException("PHP_ALLOWLIST:" . ($n + 1) . ": bad line");
            }
            $c->functions[strtolower($t)] = true;
        }
        $f = $dir . '/ACCESS_ALLOWLIST';
        if (!is_file($f)) {
            throw new RuntimeException("missing $f");
        }
        foreach (file($f, FILE_IGNORE_NEW_LINES) as $n => $line) {
            $t = trim($line);
            if ($t === '' || $t[0] === '#') {
                continue;
            }
            $parts = array_map('trim', explode('|', $t));
            $where = "ACCESS_ALLOWLIST:" . ($n + 1);
            if (count($parts) < 3 || !preg_match('/^A-[0-9]+$/', $parts[0])) {
                throw new RuntimeException("$where: bad line");
            }
            if ($parts[1] === 'E' && count($parts) === 3) {
                $c->addAccess($parts[2], $parts[0], $where);
            } elseif ($parts[1] === 'FOREACH' && count($parts) === 4 && preg_match('/^\$[A-Za-z_][A-Za-z0-9_]*$/', $parts[2])) {
                $norm = self::normalize($parts[3]);
                $c->foreach[substr($parts[2], 1)][$norm] = $parts[0];
                $c->addAccess($parts[3], $parts[0], $where);
            } else {
                throw new RuntimeException("$where: bad entry");
            }
        }
        return $c;
    }

    private function addAccess(string $expr, string $id, string $where): void
    {
        $norm = self::normalize($expr);
        $this->access[$norm] = $id;
        // A function that heads an ACCESS_ALLOWLIST entry is access-bound: every use must be an exact entry.
        if (preg_match('/^([A-Za-z_][A-Za-z0-9_]*)\(/', $norm, $m)) {
            $this->restrictedCalls[strtolower($m[1])] = true;
        }
    }

    /** Whitespace-free join of the PHP tokens of $expr. */
    public static function normalize(string $expr): string
    {
        $out = '';
        foreach (token_get_all('<?php ' . $expr) as $i => $t) {
            if ($i === 0) {
                continue;
            }
            $id = is_array($t) ? $t[0] : null;
            if ($id === T_WHITESPACE) {
                continue;
            }
            $out .= is_array($t) ? $t[1] : $t;
        }
        return $out;
    }

    public function varAllowed(string $name): bool
    {
        return in_array($name, self::BASE_VARS, true) || isset($this->foreach[$name]);
    }
}

final class Scanner
{
    /** @var list<array{stage:int,rule:string,detail:string}> */
    public array $v = [];
    private int $stage = 1;

    private const ASSIGN_TOKENS = [
        T_PLUS_EQUAL, T_MINUS_EQUAL, T_MUL_EQUAL, T_DIV_EQUAL, T_CONCAT_EQUAL, T_MOD_EQUAL, T_AND_EQUAL,
        T_OR_EQUAL, T_XOR_EQUAL, T_SL_EQUAL, T_SR_EQUAL, T_POW_EQUAL, T_COALESCE_EQUAL, T_INC, T_DEC,
    ];
    private const ALLOWED_TOKENS = [
        T_IS_IDENTICAL, T_IS_NOT_IDENTICAL, T_IS_EQUAL, T_IS_NOT_EQUAL, T_IS_GREATER_OR_EQUAL, T_IS_SMALLER_OR_EQUAL,
        T_BOOLEAN_AND, T_BOOLEAN_OR, T_DOUBLE_ARROW, T_LNUMBER, T_DNUMBER,
    ];
    private const ALLOWED_CHARS = ['!', '>', '<', ',', ')', ']'];

    public function __construct(private Cfg $cfg)
    {
    }

    private function add(string $rule, string $detail): void
    {
        $this->v[] = ['stage' => $this->stage, 'rule' => $rule, 'detail' => mb_substr($detail, 0, 160)];
    }

    // ------------------------------------------------------------------ stage 1: Blade source

    public function stage1(string $src): void
    {
        $this->stage = 1;
        if (strpos($src, '<?') !== false) {
            $this->add('php-open-tag', '<? in source');
        }
        $src = preg_replace('/\{\{--.*?--\}\}/s', '', $src) ?? '';
        $this->html($src);
        if (strpos($src, '{!!') !== false || strpos($src, '!!}') !== false) {
            $this->add('raw-echo', '{!! !!}');
        }
        $len = strlen($src);
        $pos = 0;
        while ($pos < $len) {
            $nextEcho = $this->findEcho($src, $pos);
            $nextDir = $this->findDirective($src, $pos);
            if ($nextEcho === null && $nextDir === null) {
                break;
            }
            if ($nextDir === null || ($nextEcho !== null && $nextEcho < $nextDir[0])) {
                $end = strpos($src, '}}', $nextEcho + 2);
                if ($end === false) {
                    $this->add('unterminated-echo', substr($src, $nextEcho, 40));
                    break;
                }
                $this->expr(substr($src, $nextEcho + 2, $end - $nextEcho - 2));
                $pos = $end + 2;
                continue;
            }
            [$at, $name, $after] = $nextDir;
            $pos = $after;
            $lname = $name;
            $args = null;
            $p = $after;
            while ($p < $len && ($src[$p] === ' ' || $src[$p] === "\t")) {
                $p++;
            }
            if ($p < $len && $src[$p] === '(') {
                $close = $this->balancedClose($src, $p);
                if ($close === null) {
                    $this->add('directive-not-allowed', "@$name unterminated args");
                    break;
                }
                $args = substr($src, $p + 1, $close - $p - 1);
                $pos = $close + 1;
            }
            $this->directive($lname, $args);
        }
    }

    private function findEcho(string $src, int $from): ?int
    {
        $p = $from;
        while (($i = strpos($src, '{{', $p)) !== false) {
            if ($i > 0 && $src[$i - 1] === '@') {
                $p = $i + 2;
                continue;
            }
            return $i;
        }
        return null;
    }

    /** @return array{0:int,1:string,2:int}|null */
    private function findDirective(string $src, int $from): ?array
    {
        if (preg_match('/(?<![A-Za-z0-9_@])@([A-Za-z_][A-Za-z0-9_]*)/', $src, $m, PREG_OFFSET_CAPTURE, $from)) {
            return [$m[0][1], $m[1][0], $m[0][1] + strlen($m[0][0])];
        }
        return null;
    }

    private function balancedClose(string $s, int $open): ?int
    {
        $depth = 0;
        $q = null;
        $len = strlen($s);
        for ($i = $open; $i < $len; $i++) {
            $ch = $s[$i];
            if ($q !== null) {
                if ($ch === '\\') {
                    $i++;
                } elseif ($ch === $q) {
                    $q = null;
                }
                continue;
            }
            if ($ch === "'" || $ch === '"') {
                $q = $ch;
            } elseif ($ch === '(') {
                $depth++;
            } elseif ($ch === ')') {
                $depth--;
                if ($depth === 0) {
                    return $i;
                }
            }
        }
        return null;
    }

    private function directive(string $name, ?string $args): void
    {
        $ln = $name;
        if (in_array($ln, Cfg::DIRECTIVES_NO_ARGS, true)) {
            if ($args !== null && $ln === 'empty') {
                $this->add('directive-not-allowed', '@empty with arguments');
            }
            return;
        }
        if (!in_array($ln, Cfg::DIRECTIVES_WITH_ARGS, true)) {
            $this->add('directive-not-allowed', "@$name");
            return;
        }
        if ($args === null) {
            if ($ln === 'include') {
                $this->add('include-pattern', '@include without arguments');
            } else {
                $this->add('directive-not-allowed', "@$name without arguments");
            }
            return;
        }
        switch ($ln) {
            case 'include':
                if (!preg_match("/^'selfhost\\.[a-z0-9_.-]{1,64}'$/", trim($args))) {
                    $this->add('include-pattern', "@include($args)");
                }
                break;
            case 'foreach':
            case 'forelse':
                $this->foreachHeader($args);
                break;
            default:
                $this->expr($args);
        }
    }

    private function foreachHeader(string $args): void
    {
        $T = $this->tokens($args);
        $depth = 0;
        $as = null;
        foreach ($T as $i => $t) {
            if ($t[0] === '(' || $t[0] === '[') {
                $depth++;
            } elseif ($t[0] === ')' || $t[0] === ']') {
                $depth--;
            } elseif ($t[0] === T_AS && $depth === 0) {
                $as = $i;
                break;
            }
        }
        if ($as === null) {
            $this->add('foreach-source', "no 'as' in header: $args");
            $this->exprTokens($T);
            return;
        }
        $src = array_slice($T, 0, $as);
        $rest = array_slice($T, $as + 1);
        $this->foreachCheck($src, $rest);
    }

    /** @param list<array{0:int|string,1:string}> $src @param list<array{0:int|string,1:string}> $rest */
    private function foreachCheck(array $src, array $rest): void
    {
        $srcNorm = $this->join($src);
        if (count($rest) !== 1 || $rest[0][0] !== T_VARIABLE) {
            $this->add('foreach-source', 'alias must be a single variable: ' . $this->join($rest));
        } else {
            $alias = substr($rest[0][1], 1);
            if (!isset($this->cfg->foreach[$alias][$srcNorm])) {
                $this->add('foreach-source', "source not allowed for \$$alias: $srcNorm");
            }
        }
        $this->exprTokens($src);
    }

    private function html(string $s): void
    {
        $rules = [
            'html-script' => '/<\s*script/i',
            'html-onattr' => '/(?<![A-Za-z0-9_-])on[a-z]+\s*=/i',
            'html-base' => '/<\s*base[\s>\/]/i',
            'html-meta-http-equiv' => '/<\s*meta\b[^>]*http-equiv/i',
            'html-form' => '/<\s*form/i',
            'html-iframe' => '/<\s*iframe/i',
            'html-object' => '/<\s*object/i',
            'html-embed' => '/<\s*embed/i',
            'html-link' => '/<\s*link\b/i',
            'html-javascript' => '/javascript\s*:/i',
            'html-src' => '/(?<![A-Za-z0-9_-])src\s*=/i',
            'html-style' => '/<\s*style\b|(?<![A-Za-z0-9_-])style\s*=/i',
        ];
        foreach ($rules as $rule => $re) {
            if (preg_match($re, $s, $m)) {
                $this->add($rule, trim($m[0]));
            }
        }
    }

    // ------------------------------------------------------------------ expressions

    /** @return list<array{0:int|string,1:string}> significant tokens only */
    private function tokens(string $code): array
    {
        $out = [];
        $all = token_get_all('<?php ' . $code);
        foreach ($all as $i => $t) {
            if ($i === 0) {
                continue;
            }
            $tok = is_array($t) ? [$t[0], $t[1]] : [$t, $t];
            if ($tok[0] === T_WHITESPACE) {
                continue;
            }
            $out[] = $tok;
        }
        return $out;
    }

    /** @param list<array{0:int|string,1:string}> $T */
    private function join(array $T): string
    {
        return implode('', array_map(fn($t) => $t[1], $T));
    }

    public function expr(string $code): void
    {
        $this->exprTokens($this->tokens($code));
    }

    /** @param list<array{0:int|string,1:string}> $T */
    private function exprTokens(array $T): void
    {
        $this->walk($T, 0, count($T));
    }

    /** @param list<array{0:int|string,1:string}> $T index of the matching close for the open bracket at $i */
    private function matching(array $T, int $i, int $end): ?int
    {
        $depth = 0;
        for ($j = $i; $j < $end; $j++) {
            $t = $T[$j][0];
            if ($t === '(' || $t === '[' || $t === '{' || $t === T_CURLY_OPEN || $t === T_DOLLAR_OPEN_CURLY_BRACES) {
                $depth++;
            } elseif ($t === ')' || $t === ']' || $t === '}') {
                $depth--;
                if ($depth === 0) {
                    return $j;
                }
            }
        }
        return null;
    }

    private function isValueEnd($t): bool
    {
        return $t !== null && ($t[0] === T_CONSTANT_ENCAPSED_STRING || $t[0] === T_LNUMBER || $t[0] === ')'
            || $t[0] === ']' || $t[0] === T_STRING || $t[0] === T_VARIABLE);
    }

    /** @param list<array{0:int|string,1:string}> $T */
    private function walk(array $T, int $a, int $b): void
    {
        $i = $a;
        while ($i < $b) {
            $id = $T[$i][0];
            $x = $T[$i][1];
            $prev = $i > $a ? $T[$i - 1] : null;

            if ($id === T_VARIABLE) {
                $i = $this->variable($T, $i, $b);
                continue;
            }
            if ($id === T_STRING || $id === T_NAME_QUALIFIED || $id === T_NAME_FULLY_QUALIFIED) {
                $i = $this->nameUse($T, $i, $b);
                continue;
            }
            if ($id === T_FN || $id === T_FUNCTION) {
                $this->add('closure', $x);
            } elseif ($id === T_NEW) {
                $this->add('forbidden-construct', 'new');
            } elseif (in_array($id, [T_INCLUDE, T_INCLUDE_ONCE, T_REQUIRE, T_REQUIRE_ONCE], true)) {
                $this->add('forbidden-construct', $x);
            } elseif ($id === T_EVAL) {
                $this->add('forbidden-call', 'eval');
            } elseif ($x === '`') {
                $this->add('forbidden-construct', 'backtick');
            } elseif ($id === '=' || in_array($id, self::ASSIGN_TOKENS, true)) {
                $this->add('assignment', $x);
            } elseif ($id === T_DOUBLE_COLON) {
                $this->add('static-access', '::');
            } elseif ($id === T_OBJECT_OPERATOR || $id === T_NULLSAFE_OBJECT_OPERATOR) {
                $this->add('member-not-allowed', "$x after non-chain primary");
            } elseif ($id === '{' || $id === '}' || $id === T_CURLY_OPEN || $id === T_DOLLAR_OPEN_CURLY_BRACES) {
                $this->add($id === '{' || $id === '}' ? 'brace-access' : 'interpolation', $x);
            } elseif ($id === '"' || $id === T_ENCAPSED_AND_WHITESPACE || $id === T_START_HEREDOC || $id === T_END_HEREDOC) {
                $this->add('interpolation', $x);
            } elseif ($id === '$') {
                $this->add('variable-variable', '$');
            } elseif ($id === '[') {
                if ($this->isValueEnd($prev)) {
                    $this->add('array-access', 'index after ' . $prev[1]);
                }
            } elseif ($id === '(') {
                if ($prev !== null && ($prev[0] === ')' || $prev[0] === ']' || $prev[0] === T_CONSTANT_ENCAPSED_STRING
                        || $prev[0] === T_LNUMBER)) {
                    $this->add('call-nonname', 'call on ' . $prev[1]);
                }
            } elseif ($id === T_CONSTANT_ENCAPSED_STRING) {
                $v = substr($x, 1, -1);
                if ($v !== '' && $v[0] === '/' && $v !== '/books') {
                    $this->add('slash-string', $x);
                }
            } elseif ($id === T_ELLIPSIS) {
                $this->add('token-not-allowed', '... (spread)');
            } elseif ($id === T_OPEN_TAG || $id === T_OPEN_TAG_WITH_ECHO || $id === T_CLOSE_TAG) {
                $this->add('php-open-tag', $x);
            } elseif (in_array($id, self::ALLOWED_TOKENS, true) || (is_string($id) && in_array($id, self::ALLOWED_CHARS, true))) {
                // operators and punctuation explicitly allowed
            } else {
                $this->add('token-not-allowed', is_int($id) ? token_name($id) . " $x" : $x);
            }
            $i++;
        }
    }

    /** Variable plus optional postfix chain. Returns the index after the chain. */
    private function variable(array $T, int $i, int $b): int
    {
        $name = substr($T[$i][1], 1);
        if (!$this->cfg->varAllowed($name)) {
            $this->add('var-not-allowed', $T[$i][1]);
            if ($this->stage === 2 && strncmp($name, '__', 2) === 0) {
                $this->add('s2-env-misuse', 'compiler variable outside a template: ' . $T[$i][1]);
            }
        }
        return $this->chain($T, $i, $i + 1, $b);
    }

    /** Consume `->member`, `->method(...)`, and illegal postfixes starting at $j; check the chain text. */
    private function chain(array $T, int $start, int $j, int $b): int
    {
        $postfix = false;
        $argRanges = [];
        while ($j < $b) {
            $t = $T[$j][0];
            if ($t === T_OBJECT_OPERATOR || $t === T_NULLSAFE_OBJECT_OPERATOR) {
                $postfix = true;
                $j++;
                if ($j < $b && $T[$j][0] === T_STRING) {
                    $j++;
                    if ($j < $b && $T[$j][0] === '(') {
                        $c = $this->matching($T, $j, $b);
                        if ($c === null) {
                            $this->add('s2-unbalanced', 'unbalanced method call');
                            return $b;
                        }
                        if ($j + 2 === $c && $T[$j + 1][0] === T_ELLIPSIS) {
                            $this->add('call-nonname', 'first-class callable syntax');
                        }
                        $argRanges[] = [$j + 1, $c];
                        $j = $c + 1;
                    }
                    continue;
                }
                $this->add('member-not-allowed', 'dynamic member name');
                return $b;
            }
            if ($t === T_DOUBLE_COLON) {
                $this->add('static-access', '::');
                $j++;
                if ($j < $b) {
                    if ($T[$j][0] === T_STRING) {
                        $nm = strtolower($T[$j][1]);
                        if (in_array($nm, Cfg::FORBIDDEN_NAMES, true)) {
                            $this->add('forbidden-construct', $T[$j][1]);
                        }
                    }
                    $j++;
                }
                if ($j < $b && $T[$j][0] === '(') {
                    $c = $this->matching($T, $j, $b);
                    $j = ($c ?? $b - 1) + 1;
                }
                continue;
            }
            if ($t === '[') {
                $this->add('array-access', 'index on ' . $this->join(array_slice($T, $start, $j - $start)));
                $c = $this->matching($T, $j, $b);
                $j = ($c ?? $b - 1) + 1;
                continue;
            }
            if ($t === '{') {
                $this->add('brace-access', '{');
                $c = $this->matching($T, $j, $b);
                $j = ($c ?? $b - 1) + 1;
                continue;
            }
            if ($t === '(') {
                $this->add('call-nonname', 'call on ' . $this->join(array_slice($T, $start, $j - $start)));
                $c = $this->matching($T, $j, $b);
                $j = ($c ?? $b - 1) + 1;
                continue;
            }
            break;
        }
        if ($postfix) {
            $norm = $this->join(array_slice($T, $start, $j - $start));
            if (!isset($this->cfg->access[$norm])) {
                $this->add('member-not-allowed', $norm);
                // arguments of a chain that is not allowed are still scanned (closures, calls, ...)
                foreach ($argRanges as [$from, $to]) {
                    $this->walk($T, $from, $to);
                }
            }
        }
        return $j;
    }

    /** Function call, constant or class-name use starting with a name token. */
    private function nameUse(array $T, int $i, int $b): int
    {
        $id = $T[$i][0];
        $raw = $T[$i][1];
        $lower = strtolower(ltrim($raw, '\\'));
        $segs = explode('\\', $lower);
        $last = end($segs);
        $next = $T[$i + 1] ?? null;
        if ($i + 1 >= $b) {
            $next = null;
        }

        if ($next !== null && $next[0] === '(') {
            $close = $this->matching($T, $i + 1, $b);
            if ($close === null) {
                $this->add('s2-unbalanced', "unbalanced call to $raw");
                return $b;
            }
            $inner = array_slice($T, $i + 2, $close - $i - 2);
            if (count($inner) === 1 && $inner[0][0] === T_ELLIPSIS) {
                $this->add('call-nonname', "$raw(...) first-class callable");
            }
            if ($lower === 'env' || $lower === 'getenv') {
                $ok = count($inner) === 1 && $inner[0][0] === T_CONSTANT_ENCAPSED_STRING
                    && in_array(substr($inner[0][1], 1, -1), Cfg::ENV_NAMES, true)
                    && $inner[0][1][0] === "'";
                if (!$ok) {
                    $this->add('env-arg', $raw . '(' . $this->join($inner) . ')');
                }
            }
            if (in_array($lower, Cfg::FORBIDDEN_CALLS, true)) {
                $this->add('forbidden-call', $raw);
            }
            if (in_array($last, Cfg::FORBIDDEN_NAMES, true)) {
                $this->add('forbidden-construct', $raw);
            }
            if (!isset($this->cfg->functions[$lower])) {
                $this->add('call-not-allowed', $raw);
            }
            // arguments: checked as expressions
            $this->walk($T, $i + 2, $close);
            // postfix chain on the call result (the whole text must be an ACCESS_ALLOWLIST entry)
            $end = $this->chain($T, $i, $close + 1, $b);
            if ($end === $close + 1 && isset($this->cfg->restrictedCalls[$lower])) {
                $norm = $this->join(array_slice($T, $i, $close + 1 - $i));
                if (!isset($this->cfg->access[$norm])) {
                    $this->add('member-not-allowed', $norm);
                }
            }
            return $end;
        }

        if ($next !== null && $next[0] === T_DOUBLE_COLON) {
            if (in_array($last, Cfg::FORBIDDEN_NAMES, true)) {
                $this->add('forbidden-construct', $raw);
            }
            return $this->chain($T, $i, $i + 1, $b);
        }

        if (in_array($last, Cfg::FORBIDDEN_NAMES, true)) {
            $this->add('forbidden-construct', $raw);
        }
        if ($id !== T_STRING || !in_array($lower, ['true', 'false', 'null'], true)) {
            $this->add('constant-not-allowed', $raw);
        }
        return $i + 1;
    }

    // ------------------------------------------------------------------ stage 2: compiled output

    public function stage2(string $php): void
    {
        $this->stage = 2;
        $rest = preg_replace_callback('/<\?php(.*?)\?>/s', function ($m) {
            $this->block(trim($m[1]));
            return '';
        }, $php) ?? '';
        if (strpos($rest, '<?') !== false) {
            $this->add('php-open-tag', 'PHP open tag outside a compiler-shaped block');
        }
    }

    private function block(string $body): void
    {
        $tpl = [
            'echo' => '/^echo e\((.*)\);$/s',
            'if' => '/^(?:if|elseif) ?\((.*)\):$/s',
        ];
        if ($body === 'else:' || $body === 'endif;') {
            return;
        }
        if (preg_match("/^echo \\\$__env->make\\('(selfhost\\.[a-z0-9_.-]{1,64})', array_diff_key\\(get_defined_vars\\(\\), \\['__data' => 1, '__path' => 1\\]\\)\\)->render\\(\\);\$/", $body)) {
            return;
        }
        if (preg_match('/^endforeach; \$__env->popLoop\(\); \$loop = \$__env->getLastLoop\(\);(?: if \(\$__empty_\d+\):)?$/', $body)) {
            return;
        }
        $loopRe = '/^(?:\$__empty_(\d+) = true; )?\$__currentLoopData = (.*); \$__env->addLoop\(\$__currentLoopData\); '
            . 'foreach\(\$__currentLoopData as (\$[A-Za-z_][A-Za-z0-9_]*)\): \$__env->incrementLoopIndices\(\); '
            . '\$loop = \$__env->getLastLoop\(\);(?: \$__empty_\1 = false;)?$/s';
        if (preg_match($loopRe, $body, $m)) {
            $T = $this->tokens($m[2]);
            if (!$this->shapeOk($T)) {
                $this->add('s2-unbalanced', 'loop source: ' . $m[2]);
                return;
            }
            $this->foreachCheck($T, [[T_VARIABLE, $m[3]]]);
            return;
        }
        if (preg_match($tpl['echo'], $body, $m) || preg_match($tpl['if'], $body, $m)) {
            $T = $this->tokens($m[1]);
            if (!$this->shapeOk($T)) {
                $this->add('s2-unbalanced', 'payload: ' . $m[1]);
                return;
            }
            // @isset($x) compiles to if(isset($x))
            if (isset($T[0]) && $T[0][0] === T_ISSET && ($T[1][0] ?? null) === '(' && end($T)[0] === ')') {
                $T = array_slice($T, 2, -1);
            }
            $this->exprTokens($T);
            return;
        }
        // Anything else is not a compiler template: scan it like source, and name the $__env misuse.
        $T = $this->tokens($body);
        foreach ($T as $t) {
            if ($t[0] === T_VARIABLE && strncmp($t[1], '$__', 3) === 0) {
                $this->add('s2-env-misuse', 'non-template use of ' . $t[1]);
                break;
            }
        }
        $this->exprTokens($T);
    }

    /** Payload must be one expression: balanced brackets, never negative, no statement separator. */
    private function shapeOk(array $T): bool
    {
        $depth = 0;
        foreach ($T as $t) {
            if ($t[0] === ';') {
                return false;
            }
            if ($t[0] === '(' || $t[0] === '[' || $t[0] === '{') {
                $depth++;
            } elseif ($t[0] === ')' || $t[0] === ']' || $t[0] === '}') {
                if (--$depth < 0) {
                    return false;
                }
            }
        }
        return $depth === 0;
    }
}

function compile_blade(string $src): string
{
    require_once '/app/www/vendor/autoload.php';
    $c = new Illuminate\View\Compilers\BladeCompiler(new Illuminate\Filesystem\Filesystem(), '/tmp');
    return $c->compileString($src);
}

function collect_files(string $path): array
{
    if (is_file($path)) {
        return [$path];
    }
    $out = [];
    $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($path, FilesystemIterator::SKIP_DOTS));
    foreach ($it as $f) {
        $n = $f->getPathname();
        if (substr($n, -10) === '.blade.php' || substr($n, -13) === '.compiled.php') {
            $out[] = $n;
        }
    }
    sort($out);
    return $out;
}

// ---------------------------------------------------------------------- main
$argv0 = $argv;
array_shift($argv0);
$result = ['results' => [], 'config_error' => null];
try {
    if (count($argv0) < 2) {
        throw new RuntimeException('usage: scan.php <allowlist-dir> <path>...');
    }
    $cfg = Cfg::load(array_shift($argv0));
    $files = [];
    foreach ($argv0 as $p) {
        foreach (collect_files($p) as $f) {
            $files[$f] = true;
        }
    }
    foreach (array_keys($files) as $f) {
        $sc = new Scanner($cfg);
        $src = file_get_contents($f);
        if (substr($f, -13) === '.compiled.php') {
            $sc->stage2($src);
        } else {
            $sc->stage1($src);
            try {
                $sc->stage2(compile_blade($src));
            } catch (Throwable $e) {
                $sc->v[] = ['stage' => 2, 'rule' => 's2-compile-error', 'detail' => get_class($e) . ': ' . $e->getMessage()];
            }
        }
        $result['results'][$f] = $sc->v;
    }
} catch (Throwable $e) {
    $result['config_error'] = $e->getMessage();
}
echo json_encode($result, JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR), "\n";
