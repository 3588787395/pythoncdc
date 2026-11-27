# b1: format-spec/JoinedStr dict-ladder battery — probe candidate
def b_spec_name(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w}}'
    return ''


def b_spec_call(a, b):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{len(str(b))}}'
    return ''


def b_spec_boolop(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w and 3}}'
    return ''


def b_spec_compare(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w < 3}}'
    return ''


def b_spec_unaryop(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{-w}}'
    return ''


def b_spec_subscript(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w[1]}}'
    return ''


def b_spec_slice(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w[1:2]}}'
    return ''


def b_spec_listcomp(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{[k for k in w]}}'
    return ''


def b_spec_setcomp(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{ {k % 2 for k in w} }}'
    return ''


def b_spec_dictcomp(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{ {k: k * 2 for k in w} }}'
    return ''


def b_spec_genexp(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(k + 1 for k in w)}}'
    return ''


def b_spec_dict(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{ {"x": 1} }}'
    return ''


def b_spec_list(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{ [1, 2] }}'
    return ''


def b_spec_set(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{ {1, 2} }}'
    return ''


def b_spec_tuple(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{ (1, 2) }}'
    return ''


def b_spec_attr(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w.real}}'
    return ''


def b_spec_walrus(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(q := w)}}'
    return ''


def b_spec_starred(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{max(*w)}}'
    return ''


def b_isnone(a):
    while a is None:
        a = 1
    return a


def b_isnotnone(b):
    while b is not None:
        b = None
    return b


def b_setcomp_ret(a, w):
    for i in range(3):
        if i:
            while i:
                return {k % 2 for k in w}
    return set()


def b_spec_lambda(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(lambda q: q)(w)}}'
    return ''


def b_spec_lambda2(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:{(lambda q: q)}}'
    return ''


def b_spec_nested_f(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{f"{w}"}}'
    return ''


def b_bare_fv(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{w}'
    return ''


def b_bare_fv_assign(a, w):
    r = f'{w}'
    for i in range(3):
        if i:
            while i:
                r = f'{w!r}'
    return r


def b_sole_genexp(a, w):
    for i in range(3):
        if i:
            while i:
                return sum(k + 1 for k in w)
    return 0


def b_spec_not(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{not w}}'
    return ''


def b_spec_tuple_nc(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(a, 2)}}'
    return ''


def b_spec_iter_cplx(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{[k for k in (w or [])]}}'
    return ''


def b_spec_fv_conv(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{f"{w!r}"}}'
    return ''


def b_fv_value_f(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{f"{w}"}'
    return ''


def b_spec_lambda_kwarg(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{sorted(w, key=lambda v: -v)}}'
    return ''


def b_spec_lambda_nested(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(lambda x: (lambda y: x + y))(1)(2)}}'
    return ''


def b_spec_lambda_listcomp(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{[g(1) for g in [lambda v: v + w]]}}'
    return ''


def b_genexp_sole_in_f(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{sum(x + 1 for x in w)}}'
    return ''


def b_spec_multif(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{f"x{w}y"}}'
    return ''


def b_spec_multif2(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{f"p{a}q{w}r"}'
    return ''


def b_slice_assign(a, w):
    for i in range(3):
        if i:
            while i:
                w[1:2] = [a, a]
    return w


def b_slice_del(a, w):
    for i in range(3):
        if i:
            while i:
                del w[1:2]
    return w


def b_slice_ret(a, w):
    for i in range(3):
        if i:
            while i:
                return w[a:a + 2]
    return w


async def b_spec_await(g, a):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{await g()}}'
    return ''


def b_spec_yield(i, w):
    for j in range(3):
        if j:
            while j:
                return f'{j:>{(yield w)}}'
    yield i


def b_spec_yieldfrom(i, w):
    for j in range(3):
        if j:
            while j:
                return f'{j:>{(yield from w)}}'
    yield i


def b_spec_invert(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{~w}}'
    return ''


def b_spec_positive(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{+w}}'
    return ''


def b_match_seqlen(a, w):
    for i in range(3):
        if i:
            while i:
                match w:
                    case [p, q]:
                        return p + a
                    case _:
                        return 0
    return -1

def b_bigfunc_deep(a):
    for i in range(3):
        if i:
            while i:
                v000 = a
                v001 = a
                v002 = a
                v003 = a
                v004 = a
                v005 = a
                v006 = a
                v007 = a
                v008 = a
                v009 = a
                v010 = a
                v011 = a
                v012 = a
                v013 = a
                v014 = a
                v015 = a
                v016 = a
                v017 = a
                v018 = a
                v019 = a
                v020 = a
                v021 = a
                v022 = a
                v023 = a
                v024 = a
                v025 = a
                v026 = a
                v027 = a
                v028 = a
                v029 = a
                v030 = a
                v031 = a
                v032 = a
                v033 = a
                v034 = a
                v035 = a
                v036 = a
                v037 = a
                v038 = a
                v039 = a
                v040 = a
                v041 = a
                v042 = a
                v043 = a
                v044 = a
                v045 = a
                v046 = a
                v047 = a
                v048 = a
                v049 = a
                v050 = a
                v051 = a
                v052 = a
                v053 = a
                v054 = a
                v055 = a
                v056 = a
                v057 = a
                v058 = a
                v059 = a
                v060 = a
                v061 = a
                v062 = a
                v063 = a
                v064 = a
                v065 = a
                v066 = a
                v067 = a
                v068 = a
                v069 = a
                v070 = a
                v071 = a
                v072 = a
                v073 = a
                v074 = a
                v075 = a
                v076 = a
                v077 = a
                v078 = a
                v079 = a
                v080 = a
                v081 = a
                v082 = a
                v083 = a
                v084 = a
                v085 = a
                v086 = a
                v087 = a
                v088 = a
                v089 = a
                v090 = a
                v091 = a
                v092 = a
                v093 = a
                v094 = a
                v095 = a
                v096 = a
                v097 = a
                v098 = a
                v099 = a
                v100 = a
                v101 = a
                v102 = a
                v103 = a
                v104 = a
                v105 = a
                v106 = a
                v107 = a
                v108 = a
                v109 = a
                v110 = a
                v111 = a
                v112 = a
                v113 = a
                v114 = a
                v115 = a
                v116 = a
                v117 = a
                v118 = a
                v119 = a
                v120 = a
                v121 = a
                v122 = a
                v123 = a
                v124 = a
                v125 = a
                v126 = a
                v127 = a
                v128 = a
                v129 = a
                v130 = a
                v131 = a
                v132 = a
                v133 = a
                v134 = a
                v135 = a
                v136 = a
                v137 = a
                v138 = a
                v139 = a
                v140 = a
                v141 = a
                v142 = a
                v143 = a
                v144 = a
                v145 = a
                v146 = a
                v147 = a
                v148 = a
                v149 = a
                v150 = a
                v151 = a
                v152 = a
                v153 = a
                v154 = a
                v155 = a
                v156 = a
                v157 = a
                v158 = a
                v159 = a
                v160 = a
                v161 = a
                v162 = a
                v163 = a
                v164 = a
                v165 = a
                v166 = a
                v167 = a
                v168 = a
                v169 = a
                v170 = a
                v171 = a
                v172 = a
                v173 = a
                v174 = a
                v175 = a
                v176 = a
                v177 = a
                v178 = a
                v179 = a
                v180 = a
                v181 = a
                v182 = a
                v183 = a
                v184 = a
                v185 = a
                v186 = a
                v187 = a
                v188 = a
                v189 = a
                v190 = a
                v191 = a
                v192 = a
                v193 = a
                v194 = a
                v195 = a
                v196 = a
                v197 = a
                v198 = a
                v199 = a
                v200 = a
                v201 = a
                v202 = a
                v203 = a
                v204 = a
                v205 = a
                v206 = a
                v207 = a
                v208 = a
                v209 = a
                v210 = a
                v211 = a
                v212 = a
                v213 = a
                v214 = a
                v215 = a
                v216 = a
                v217 = a
                v218 = a
                v219 = a
                v220 = a
                v221 = a
                v222 = a
                v223 = a
                v224 = a
                v225 = a
                v226 = a
                v227 = a
                v228 = a
                v229 = a
                v230 = a
                v231 = a
                v232 = a
                v233 = a
                v234 = a
                v235 = a
                v236 = a
                v237 = a
                v238 = a
                v239 = a
                v240 = a
                v241 = a
                v242 = a
                v243 = a
                v244 = a
                v245 = a
                v246 = a
                v247 = a
                v248 = a
                v249 = a
                v250 = a
                v251 = a
                v252 = a
                v253 = a
                v254 = a
                v255 = a
                v256 = a
                v257 = a
                v258 = a
                v259 = a
                return (v259, v000)
    return a
