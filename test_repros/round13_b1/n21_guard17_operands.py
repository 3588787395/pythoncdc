def n21_attr(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or a.attr)}}'
    return ''


def n21_list(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or [b, w])}}'
    return ''


def n21_set(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or {b, w})}}'
    return ''


def n21_tuple(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or (b, w))}}'
    return ''


def n21_subscript(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or w[1])}}'
    return ''


def n21_listcomp(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or [q + 1 for q in w])}}'
    return ''


def n21_setcomp(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or {q + 1 for q in w})}}'
    return ''


def n21_dictcomp(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or {q: q + 1 for q in w})}}'
    return ''


def n21_genexp(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or (q + 1 for q in w))}}'
    return ''


def n21_joinedstr(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or f"x{b}y")}}'
    return ''


def n21_fv(a, b, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{(i or f"{b!r}")}}'
    return ''


def n21_unary_attr(a, b, w):
    for i in range(3):
        if i:
            while i:
                if not a.attr:
                    return f'{a:>{-a.attr}}'
    return 0


def n21_unary_comp(a, b, w):
    for i in range(3):
        if i:
            while i:
                r = [q for q in w if not q]
                return f'{a:>{~len(r)}}'
    return 0


def n21_setcomp_plain(w):
    s = {q + 1 for q in w}
    while s:
        return s
    return set()


def n21_pjbi_notnone(w):
    while w is not None:
        return w
    return 0


def n21_del_deref(a, w):
    y = 1

    def inner():
        nonlocal y
        for i in range(3):
            if i:
                while i:
                    del y
                    return i
        return 0

    return inner()


def n21_del_global(a, w):
    global n21_gv
    for i in range(3):
        if i:
            while i:
                n21_gv = i
                del n21_gv
                return i
    return 0


def n21_match_getlen(a, w):
    for i in range(3):
        if i:
            while i:
                match w:
                    case []:
                        return a
                    case [p, q]:
                        return p
                    case _:
                        return 0
    return -1


n21_gv = 0
n21_mod_setcomp = {q + 1 for q in range(5)}

def b_extarg_cond(a):
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
                while v259:
                    return v259
    return a
