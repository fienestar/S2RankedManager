"""Korean patch helpers for SpelunkyRanked files."""

from __future__ import annotations

import re
from pathlib import Path

_FONT_STYLE_TOKEN = "VANILLA_FONT_STYLE.ITALIC"
_KOREAN_FONT_STYLE_VALUE = "13"
_PATCHED_MARKER = "inputs.ALLOWED_CHAT_INPUT = "
_INPUT_BLOCK_RE = re.compile(
    r"(?m)"
    r"(?:^ {8}if input\.keypressed\((?:[^\r\n]+)\) or input\.keypressed\((?:[^\r\n]+)\) then\r?\n"
    r"^ {12}addToMessage\((?:[^\r\n]+)\)\r?\n"
    r"^ {8}end\r?\n?)+"
)

_INPUT_BLOCK_NEW_BODY = """if inputs.korean_toggle == nil then
    inputs.korean_toggle = false
    inputs.ALLOWED_CHAT_INPUT = [[ -=+*/\\|/.,;'":<>{}[]`~?!@#$%^&*()_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789]]
    inputs.ALPHABET_CHAT_INPUT = "abcdefghijklmnopqrstuvwxyz"
    inputs.KEY_INPUTS = {
        {32, " ", " "},
        {65, "a", "A"}, {66, "b", "B"}, {67, "c", "C"}, {68, "d", "D"}, {69, "e", "E"},
        {70, "f", "F"}, {71, "g", "G"}, {72, "h", "H"}, {73, "i", "I"}, {74, "j", "J"},
        {75, "k", "K"}, {76, "l", "L"}, {77, "m", "M"}, {78, "n", "N"}, {79, "o", "O"},
        {80, "p", "P"}, {81, "q", "Q"}, {82, "r", "R"}, {83, "s", "S"}, {84, "t", "T"},
        {85, "u", "U"}, {86, "v", "V"}, {87, "w", "W"}, {88, "x", "X"}, {89, "y", "Y"},
        {90, "z", "Z"},
        {48, "0", ")"}, {49, "1", "!"}, {50, "2", "@"}, {51, "3", "#"}, {52, "4", "$"},
        {53, "5", "%"}, {54, "6", "^"}, {55, "7", "&"}, {56, "8", "*"}, {57, "9", "("},
        {192, "`", "~"}, {189, "-", "_"}, {187, "=", "+"}, {219, "[", "{"}, {221, "]", "}"},
        {220, "\\\\"", "|"}, {186, ";", ":"}, {222, "'", '"'}, {188, ",", "<"}, {190, ".", ">"},
        {191, "/", "?"}
    }
    inputs.CHAR_MAP = {}
    for i = 1, #inputs.KEY_INPUTS do
        local entry = inputs.KEY_INPUTS[i]
        inputs.CHAR_MAP[entry[2]] = entry[2]
        inputs.CHAR_MAP[entry[3]] = entry[3]
    end

    local koreanValues = {
        string.char(0xE3, 0x85, 0x81), string.char(0xE3, 0x85, 0xA0),
        string.char(0xE3, 0x85, 0x8A), string.char(0xE3, 0x85, 0x87),
        string.char(0xE3, 0x84, 0xB7), string.char(0xE3, 0x84, 0xB9),
        string.char(0xE3, 0x85, 0x8E), string.char(0xE3, 0x85, 0x97),
        string.char(0xE3, 0x85, 0x91), string.char(0xE3, 0x85, 0x93),
        string.char(0xE3, 0x85, 0x8F), string.char(0xE3, 0x85, 0xA3),
        string.char(0xE3, 0x85, 0xA1), string.char(0xE3, 0x85, 0x9C),
        string.char(0xE3, 0x85, 0x90), string.char(0xE3, 0x85, 0x94),
        string.char(0xE3, 0x85, 0x82), string.char(0xE3, 0x84, 0xB1),
        string.char(0xE3, 0x84, 0xB4), string.char(0xE3, 0x85, 0x85),
        string.char(0xE3, 0x85, 0x95), string.char(0xE3, 0x85, 0x8D),
        string.char(0xE3, 0x85, 0x88), string.char(0xE3, 0x85, 0x8C),
        string.char(0xE3, 0x85, 0x9B), string.char(0xE3, 0x85, 0x8B)
    }
    inputs.KOREAN_MAP = {}
    for i = 1, #inputs.ALPHABET_CHAT_INPUT do
        local ch = string.sub(inputs.ALPHABET_CHAT_INPUT, i, i)
        inputs.KOREAN_MAP[ch] = koreanValues[i]
    end

    inputs.KOREAN_L_KEY = {
        r = 0, s = 2, e = 3, f = 5, a = 6, q = 7, t = 9,
        d = 11, w = 12, c = 14, z = 15, x = 16, v = 17, g = 18
    }
    inputs.KOREAN_SHIFT_L_KEY = {r = 1, e = 4, q = 8, t = 10, w = 13}
    inputs.KOREAN_V_KEY = {k = 0, o = 1, i = 2, j = 4, p = 5, u = 6, h = 8, y = 12, n = 13, b = 17, m = 18, l = 20}
    inputs.KOREAN_SHIFT_V_KEY = {o = 3, p = 7}
    inputs.KOREAN_T_KEY = {
        r = 1, s = 4, e = 7, f = 8, a = 16, q = 17, t = 19,
        d = 21, w = 22, c = 23, z = 24, x = 25, v = 26, g = 27
    }
    inputs.KOREAN_T_TO_L = {[1] = 0, [4] = 2, [7] = 3, [8] = 5, [16] = 6, [17] = 7, [19] = 9, [21] = 11, [22] = 12, [23] = 14, [24] = 15, [25] = 16, [26] = 17, [27] = 18}
    inputs.KOREAN_V_COMBINE = {
        ["8:0"] = 9, ["8:1"] = 10, ["8:20"] = 11,
        ["13:4"] = 14, ["13:5"] = 15, ["13:20"] = 16,
        ["18:20"] = 19
    }
    inputs.KOREAN_L_COMPAT = {
        [0] = string.char(0xE3, 0x84, 0xB1), [1] = string.char(0xE3, 0x84, 0xB2), [2] = string.char(0xE3, 0x84, 0xB4),
        [3] = string.char(0xE3, 0x84, 0xB7), [4] = string.char(0xE3, 0x84, 0xB8), [5] = string.char(0xE3, 0x84, 0xB9),
        [6] = string.char(0xE3, 0x85, 0x81), [7] = string.char(0xE3, 0x85, 0x82), [8] = string.char(0xE3, 0x85, 0x83),
        [9] = string.char(0xE3, 0x85, 0x85), [10] = string.char(0xE3, 0x85, 0x86), [11] = string.char(0xE3, 0x85, 0x87),
        [12] = string.char(0xE3, 0x85, 0x88), [13] = string.char(0xE3, 0x85, 0x89), [14] = string.char(0xE3, 0x85, 0x8A),
        [15] = string.char(0xE3, 0x85, 0x8B), [16] = string.char(0xE3, 0x85, 0x8C), [17] = string.char(0xE3, 0x85, 0x8D),
        [18] = string.char(0xE3, 0x85, 0x8E)
    }
    inputs.KOREAN_V_COMPAT = {
        [0] = string.char(0xE3, 0x85, 0x8F), [1] = string.char(0xE3, 0x85, 0x90), [2] = string.char(0xE3, 0x85, 0x91),
        [3] = string.char(0xE3, 0x85, 0x92), [4] = string.char(0xE3, 0x85, 0x93), [5] = string.char(0xE3, 0x85, 0x94),
        [6] = string.char(0xE3, 0x85, 0x95), [7] = string.char(0xE3, 0x85, 0x96), [8] = string.char(0xE3, 0x85, 0x97),
        [9] = string.char(0xE3, 0x85, 0x98), [10] = string.char(0xE3, 0x85, 0x99), [11] = string.char(0xE3, 0x85, 0x9A),
        [12] = string.char(0xE3, 0x85, 0x9B), [13] = string.char(0xE3, 0x85, 0x9C), [14] = string.char(0xE3, 0x85, 0x9D),
        [15] = string.char(0xE3, 0x85, 0x9E), [16] = string.char(0xE3, 0x85, 0x9F), [17] = string.char(0xE3, 0x85, 0xA0),
        [18] = string.char(0xE3, 0x85, 0xA1), [19] = string.char(0xE3, 0x85, 0xA2), [20] = string.char(0xE3, 0x85, 0xA3)
    }
    inputs.KOREAN_STATE = {L = nil, V = nil, T = nil, preview_active = false}

    function inputs.korean_utf8_char(codepoint)
        if codepoint <= 0x7F then
            return string.char(codepoint)
        elseif codepoint <= 0x7FF then
            return string.char(
                0xC0 + math.floor(codepoint / 0x40),
                0x80 + (codepoint % 0x40)
            )
        elseif codepoint <= 0xFFFF then
            return string.char(
                0xE0 + math.floor(codepoint / 0x1000),
                0x80 + (math.floor(codepoint / 0x40) % 0x40),
                0x80 + (codepoint % 0x40)
            )
        end
        return string.char(
            0xF0 + math.floor(codepoint / 0x40000),
            0x80 + (math.floor(codepoint / 0x1000) % 0x40),
            0x80 + (math.floor(codepoint / 0x40) % 0x40),
            0x80 + (codepoint % 0x40)
        )
    end

    function inputs.korean_can_append(str)
        return str ~= nil and (#chatMessage + #str) <= 50
    end

    function inputs.korean_trim_last_char(str)
        local i = #str
        if i == 0 then
            return str
        end
        while i > 0 do
            local b = string.byte(str, i)
            if b < 0x80 or b >= 0xC0 then
                return string.sub(str, 1, i - 1)
            end
            i = i - 1
        end
        return ""
    end

    function inputs.korean_preview_char()
        local st = inputs.KOREAN_STATE
        if st.L ~= nil and st.V ~= nil then
            local t = st.T or 0
            local codepoint = 0xAC00 + ((st.L * 21) + st.V) * 28 + t
            return inputs.korean_utf8_char(codepoint)
        end
        if st.L ~= nil then
            return inputs.KOREAN_L_COMPAT[st.L]
        end
        if st.V ~= nil then
            return inputs.KOREAN_V_COMPAT[st.V]
        end
        return nil
    end

    function inputs.korean_render_preview()
        local st = inputs.KOREAN_STATE
        local preview = inputs.korean_preview_char()
        if st.preview_active then
            chatMessage = inputs.korean_trim_last_char(chatMessage)
        end
        if inputs.korean_can_append(preview) then
            chatMessage = chatMessage..preview
            st.preview_active = true
        else
            st.preview_active = false
        end
    end

    function inputs.korean_flush_preview()
        local st = inputs.KOREAN_STATE
        st.preview_active = false
        st.L = nil
        st.V = nil
        st.T = nil
    end

    function inputs.korean_pick_l(ch, shifted)
        if shifted and inputs.KOREAN_SHIFT_L_KEY[ch] ~= nil then
            return inputs.KOREAN_SHIFT_L_KEY[ch]
        end
        return inputs.KOREAN_L_KEY[ch]
    end

    function inputs.korean_pick_v(ch, shifted)
        if shifted and inputs.KOREAN_SHIFT_V_KEY[ch] ~= nil then
            return inputs.KOREAN_SHIFT_V_KEY[ch]
        end
        return inputs.KOREAN_V_KEY[ch]
    end

    function inputs.resolve_chat_char(entry, shifted)
        if shifted then
            return entry[3]
        end
        return entry[2]
    end

    function inputs.process_korean_chat_key(ch, shifted)
        local st = inputs.KOREAN_STATE
        local is_alpha = string.match(ch, "%a") ~= nil
        if not is_alpha then
            if st.preview_active then
                inputs.korean_flush_preview()
            end
            local direct = inputs.CHAR_MAP[ch] or ch
            if inputs.korean_can_append(direct) then
                addToMessage(direct)
            end
            return
        end

        local key = string.lower(ch)
        local l = inputs.korean_pick_l(key, shifted)
        local v = inputs.korean_pick_v(key, shifted)
        local t = inputs.KOREAN_T_KEY[key]

        if v ~= nil then
            if st.L == nil and st.V == nil then
                st.V = v
                inputs.korean_render_preview()
                return
            end
            if st.L ~= nil and st.V == nil then
                st.V = v
                inputs.korean_render_preview()
                return
            end
            if st.L ~= nil and st.V ~= nil and st.T ~= nil then
                local moved_l = inputs.KOREAN_T_TO_L[st.T]
                st.T = nil
                inputs.korean_render_preview()
                inputs.korean_flush_preview()
                st.L = moved_l
                st.V = v
                st.T = nil
                inputs.korean_render_preview()
                return
            end
            if st.V ~= nil then
                local combo_key = tostring(st.V)..":"..tostring(v)
                local combined = inputs.KOREAN_V_COMBINE[combo_key]
                if combined ~= nil then
                    st.V = combined
                    inputs.korean_render_preview()
                    return
                end
                inputs.korean_flush_preview()
                st.V = v
                inputs.korean_render_preview()
                return
            end
        end

        if l ~= nil then
            if st.L == nil and st.V == nil then
                st.L = l
                st.T = nil
                inputs.korean_render_preview()
                return
            end
            if st.L ~= nil and st.V == nil then
                inputs.korean_flush_preview()
                st.L = l
                st.T = nil
                inputs.korean_render_preview()
                return
            end
            if st.L ~= nil and st.V ~= nil then
                if st.T == nil and t ~= nil then
                    st.T = t
                    inputs.korean_render_preview()
                    return
                end
                inputs.korean_flush_preview()
                st.L = l
                st.V = nil
                st.T = nil
                inputs.korean_render_preview()
                return
            end
            if st.L == nil and st.V ~= nil then
                inputs.korean_flush_preview()
                st.L = l
                st.V = nil
                st.T = nil
                inputs.korean_render_preview()
                return
            end
        end

        if st.preview_active then
            inputs.korean_flush_preview()
        end
        if inputs.korean_can_append(ch) then
            addToMessage(ch)
        end
    end
end
if inputs.key_press(20) then
    inputs.korean_toggle = not inputs.korean_toggle
    if not inputs.korean_toggle and inputs.KOREAN_STATE ~= nil and inputs.KOREAN_STATE.preview_active then
        inputs.korean_flush_preview()
    end
end
if chatMessage == "" and inputs.KOREAN_STATE ~= nil then
    local st = inputs.KOREAN_STATE
    inputs.korean_flush_preview()
end
for i = 1, #inputs.KEY_INPUTS do
    local entry = inputs.KEY_INPUTS[i]
    local keycode = entry[1]
    local pressed = inputs.key_press(keycode)
    local pressed_shifted = inputs.key_press(keycode | 512)
    if pressed or pressed_shifted then
        local shifted = pressed_shifted
        local ch = inputs.resolve_chat_char(entry, shifted)
        if inputs.korean_toggle then
            inputs.process_korean_chat_key(ch, shifted)
        else
            if inputs.KOREAN_STATE ~= nil and inputs.KOREAN_STATE.preview_active then
                inputs.korean_flush_preview()
            end
            local mapped = inputs.CHAR_MAP[ch] or ch
            if inputs.korean_can_append(mapped) then
                addToMessage(mapped)
            end
        end
    end
end"""


def patch_main_lua(text: str) -> str:
    """Patch the contents of a `main.lua` file from SpelunkyRanked."""
    patched = text

    if _FONT_STYLE_TOKEN in patched:
        patched = patched.replace(_FONT_STYLE_TOKEN, _KOREAN_FONT_STYLE_VALUE)

    if _PATCHED_MARKER not in patched:
        replacement = "\n".join(f"        {line}" for line in _INPUT_BLOCK_NEW_BODY.splitlines())
        patched, _ = _INPUT_BLOCK_RE.subn(replacement, patched, count=1)

    return patched


def patch_mod_dir(mod_dir: Path) -> bool:
    """Patch `main.lua` in a SpelunkyRanked mod directory."""
    main_lua_path = mod_dir / "main.lua"
    if not main_lua_path.exists():
        return False

    text = main_lua_path.read_text(encoding="utf-8")
    patched = patch_main_lua(text)

    if patched == text:
        return False

    main_lua_path.write_text(patched, encoding="utf-8")
    return True
