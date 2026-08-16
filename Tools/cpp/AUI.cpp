#include <windows.h>
#include <uiautomation.h>
#include <comdef.h>
#include <iostream>
#include <string>
#include <vector>
#include <cwctype>

#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "uiautomationcore.lib")


// ======================================================
// Helpers
// ======================================================

std::wstring Utf8ToWide(const std::string& str)
{
    if (str.empty())
        return std::wstring();

    int size = MultiByteToWideChar(
        CP_UTF8,
        0,
        str.c_str(),
        -1,
        nullptr,
        0
    );

    std::wstring wide(size, L'\0');

    MultiByteToWideChar(
        CP_UTF8,
        0,
        str.c_str(),
        -1,
        &wide[0],
        size
    );

    // MultiByteToWideChar's size includes the null terminator
    if (!wide.empty() && wide.back() == L'\0')
        wide.pop_back();

    return wide;
}


std::wstring JsonEscape(BSTR bstr)
{
    std::wstring s = bstr ? bstr : L"";
    std::wstring out;
    out.reserve(s.size());

    for (wchar_t c : s)
    {
        switch (c)
        {
            case L'\"': out += L"\\\""; break;
            case L'\\': out += L"\\\\"; break;
            case L'\n': out += L"\\n";  break;
            case L'\r': out += L"\\r";  break;
            case L'\t': out += L"\\t";  break;
            default:
                if (c < 0x20)
                {
                    wchar_t buf[8];
                    swprintf_s(buf, L"\\u%04x", c);
                    out += buf;
                }
                else
                {
                    out += c;
                }
        }
    }

    return out;
}


HRESULT FindElementByName(
    IUIAutomation* uia,
    IUIAutomationElement* root,
    const std::wstring& name,
    IUIAutomationElement** out)
{
    *out = nullptr;

    IUIAutomationCondition* condition = nullptr;

    VARIANT value;
    VariantInit(&value);

    value.vt = VT_BSTR;
    value.bstrVal = SysAllocString(name.c_str());

    HRESULT hr = uia->CreatePropertyCondition(
        UIA_NamePropertyId,
        value,
        &condition
    );

    VariantClear(&value);

    if (FAILED(hr))
        return hr;

    hr = root->FindFirst(
        TreeScope_Descendants,
        condition,
        out
    );

    condition->Release();

    return hr;
}


void SendKeyEvent(WORD vk, bool keyUp)
{
    INPUT input = {};

    input.type = INPUT_KEYBOARD;
    input.ki.wVk = vk;

    if (keyUp)
        input.ki.dwFlags = KEYEVENTF_KEYUP;

    SendInput(1, &input, sizeof(INPUT));
}


void SendUnicodeChar(wchar_t ch, bool keyUp)
{
    INPUT input = {};

    input.type = INPUT_KEYBOARD;
    input.ki.wScan = ch;
    input.ki.dwFlags = KEYEVENTF_UNICODE | (keyUp ? KEYEVENTF_KEYUP : 0);

    SendInput(1, &input, sizeof(INPUT));
}


void TypeText(const std::wstring& text)
{
    for (wchar_t ch : text)
    {
        SendUnicodeChar(ch, false);
        SendUnicodeChar(ch, true);
    }
}


// Maps a single key name ("ENTER", "CTRL", "A", "F5", ...) to a VK code.
// Returns 0 if the name isn't recognized.
WORD KeyNameToVK(const std::wstring& name)
{
    std::wstring upper = name;

    for (auto& c : upper)
        c = static_cast<wchar_t>(towupper(c));

    if (upper == L"ENTER" || upper == L"RETURN") return VK_RETURN;
    if (upper == L"TAB")                         return VK_TAB;
    if (upper == L"ESC" || upper == L"ESCAPE")    return VK_ESCAPE;
    if (upper == L"SPACE")                        return VK_SPACE;
    if (upper == L"BACKSPACE")                    return VK_BACK;
    if (upper == L"DELETE" || upper == L"DEL")    return VK_DELETE;
    if (upper == L"HOME")                         return VK_HOME;
    if (upper == L"END")                          return VK_END;
    if (upper == L"UP")                           return VK_UP;
    if (upper == L"DOWN")                         return VK_DOWN;
    if (upper == L"LEFT")                         return VK_LEFT;
    if (upper == L"RIGHT")                        return VK_RIGHT;
    if (upper == L"PAGEUP")                       return VK_PRIOR;
    if (upper == L"PAGEDOWN")                     return VK_NEXT;
    if (upper == L"CTRL" || upper == L"CONTROL")  return VK_CONTROL;
    if (upper == L"ALT")                          return VK_MENU;
    if (upper == L"SHIFT")                        return VK_SHIFT;
    if (upper == L"WIN")                          return VK_LWIN;

    if (upper.size() == 1)
    {
        wchar_t c = upper[0];

        if ((c >= L'0' && c <= L'9') || (c >= L'A' && c <= L'Z'))
            return static_cast<WORD>(c);
    }

    if (upper.size() >= 2 && upper[0] == L'F')
    {
        try
        {
            int n = std::stoi(upper.substr(1));

            if (n >= 1 && n <= 12)
                return static_cast<WORD>(VK_F1 + (n - 1));
        }
        catch (...)
        {
            // not an FN key, fall through
        }
    }

    return 0;
}


std::vector<std::wstring> SplitKeyChord(const std::wstring& text)
{
    std::vector<std::wstring> parts;

    size_t start = 0;
    size_t pos;

    while ((pos = text.find(L'+', start)) != std::wstring::npos)
    {
        parts.push_back(text.substr(start, pos - start));
        start = pos + 1;
    }

    parts.push_back(text.substr(start));

    return parts;
}


void PrintElementTree(
    IUIAutomationTreeWalker* walker,
    IUIAutomationElement* element,
    int depth,
    int maxDepth,
    std::wostream& out)
{
    BSTR name = nullptr;
    BSTR className = nullptr;
    BSTR controlType = nullptr;

    element->get_CurrentName(&name);
    element->get_CurrentClassName(&className);
    element->get_CurrentLocalizedControlType(&controlType);

    out
        << L"{\"name\":\"" << JsonEscape(name) << L"\","
        << L"\"class\":\"" << JsonEscape(className) << L"\","
        << L"\"type\":\"" << JsonEscape(controlType) << L"\","
        << L"\"children\":[";

    SysFreeString(name);
    SysFreeString(className);
    SysFreeString(controlType);

    if (depth < maxDepth)
    {
        IUIAutomationElement* child = nullptr;
        walker->GetFirstChildElement(element, &child);

        bool first = true;

        while (child)
        {
            if (!first)
                out << L",";

            first = false;

            PrintElementTree(walker, child, depth + 1, maxDepth, out);

            IUIAutomationElement* next = nullptr;
            walker->GetNextSiblingElement(child, &next);

            child->Release();
            child = next;
        }
    }

    out << L"]}";
}


int main(int argc, char* argv[])
{
    // --------------------------------------------------
    // Command + arguments
    // --------------------------------------------------

    std::string command = "observe";

    if (argc >= 2)
        command = argv[1];

    std::string argument1;
    std::string argument2;

    if (argc >= 3)
        argument1 = argv[2];

    if (argc >= 4)
        argument2 = argv[3];


    // --------------------------------------------------
    // COM
    // --------------------------------------------------

    HRESULT hr = CoInitializeEx(
        nullptr,
        COINIT_APARTMENTTHREADED
    );

    if (FAILED(hr))
    {
        std::cout << "{\"error\":\"COM initialization failed\"}";
        return 1;
    }


    // --------------------------------------------------
    // UI Automation
    // --------------------------------------------------

    IUIAutomation* uia = nullptr;

    hr = CoCreateInstance(
        CLSID_CUIAutomation,
        nullptr,
        CLSCTX_INPROC_SERVER,
        IID_PPV_ARGS(&uia)
    );

    if (FAILED(hr))
    {
        std::cout << "{\"error\":\"UIA initialization failed\"}";
        CoUninitialize();
        return 1;
    }


    // --------------------------------------------------
    // Desktop
    // --------------------------------------------------

    IUIAutomationElement* root = nullptr;

    hr = uia->GetRootElement(&root);

    if (FAILED(hr))
    {
        std::cout << "{\"error\":\"Could not get desktop\"}";

        uia->Release();
        CoUninitialize();

        return 1;
    }


    // ==================================================
    // OBSERVE
    // ==================================================

    if (command == "observe")
    {
        BSTR name = nullptr;

        root->get_CurrentName(&name);

        std::wcout
            << L"{\"desktop\":\""
            << (name ? name : L"")
            << L"\"}";

        SysFreeString(name);
    }


    // ==================================================
    // FIND
    // ==================================================

    else if (command == "find")
    {
        if (argument1.empty())
        {
            std::cout << "{\"error\":\"Missing search text\"}";
        }
        else
        {
            std::wstring wideSearch = Utf8ToWide(argument1);

            IUIAutomationElement* element = nullptr;
            hr = FindElementByName(uia, root, wideSearch, &element);

            if (SUCCEEDED(hr) && element)
            {
                BSTR name = nullptr;
                BSTR className = nullptr;

                RECT rect{};

                element->get_CurrentName(&name);
                element->get_CurrentClassName(&className);
                element->get_CurrentBoundingRectangle(&rect);

                std::wcout
                    << L"{"
                    << L"\"found\":true,"
                    << L"\"name\":\""
                    << (name ? name : L"")
                    << L"\","
                    << L"\"class\":\""
                    << (className ? className : L"")
                    << L"\","
                    << L"\"bbox\":["
                    << rect.left << L","
                    << rect.top << L","
                    << rect.right << L","
                    << rect.bottom
                    << L"]"
                    << L"}";

                SysFreeString(name);
                SysFreeString(className);

                element->Release();
            }
            else
            {
                std::cout << "{\"found\":false}";
            }
        }
    }


    // ==================================================
    // READ
    // ==================================================

    else if (command == "read")
    {
        if (argument1.empty())
        {
            std::cout << "{\"error\":\"Missing element name\"}";
        }
        else
        {
            std::wstring wideName = Utf8ToWide(argument1);

            IUIAutomationElement* element = nullptr;
            hr = FindElementByName(uia, root, wideName, &element);

            if (SUCCEEDED(hr) && element)
            {
                // Try ValuePattern (edit boxes, combo boxes, etc.)
                IUIAutomationValuePattern* valuePattern = nullptr;

                hr = element->GetCurrentPattern(
                    UIA_ValuePatternId,
                    reinterpret_cast<IUnknown**>(&valuePattern)
                );

                if (SUCCEEDED(hr) && valuePattern)
                {
                    BSTR value = nullptr;
                    valuePattern->get_CurrentValue(&value);

                    std::wcout
                        << L"{\"read\":true,\"pattern\":\"ValuePattern\",\"value\":\""
                        << (value ? value : L"")
                        << L"\"}";

                    SysFreeString(value);
                    valuePattern->Release();
                }
                else
                {
                    // Fall back to TextPattern (documents, rich text)
                    IUIAutomationTextPattern* textPattern = nullptr;

                    hr = element->GetCurrentPattern(
                        UIA_TextPatternId,
                        reinterpret_cast<IUnknown**>(&textPattern)
                    );

                    if (SUCCEEDED(hr) && textPattern)
                    {
                        IUIAutomationTextRange* range = nullptr;
                        hr = textPattern->get_DocumentRange(&range);

                        if (SUCCEEDED(hr) && range)
                        {
                            BSTR text = nullptr;
                            range->GetText(-1, &text);

                            std::wcout
                                << L"{\"read\":true,\"pattern\":\"TextPattern\",\"value\":\""
                                << (text ? text : L"")
                                << L"\"}";

                            SysFreeString(text);
                            range->Release();
                        }
                        else
                        {
                            std::cout
                                << "{\"read\":false,\"error\":\"Could not get text range\"}";
                        }

                        textPattern->Release();
                    }
                    else
                    {
                        // Last resort: the accessible Name
                        BSTR name = nullptr;
                        element->get_CurrentName(&name);

                        std::wcout
                            << L"{\"read\":true,\"pattern\":\"Name\",\"value\":\""
                            << (name ? name : L"")
                            << L"\"}";

                        SysFreeString(name);
                    }
                }

                element->Release();
            }
            else
            {
                std::cout
                    << "{\"read\":false,\"error\":\"Element not found\"}";
            }
        }
    }


    // ==================================================
    // CLICK
    // ==================================================

    else if (command == "click")
    {
        if (argument1.empty())
        {
            std::cout
                << "{\"error\":\"Missing element name\"}";
        }
        else
        {
            std::wstring wideName = Utf8ToWide(argument1);

            IUIAutomationElement* element = nullptr;
            hr = FindElementByName(uia, root, wideName, &element);

            if (SUCCEEDED(hr) && element)
            {
                // Try InvokePattern first (buttons, menu items,
                // links, etc.)
                IUIAutomationInvokePattern* invoke = nullptr;

                hr = element->GetCurrentPattern(
                    UIA_InvokePatternId,
                    reinterpret_cast<IUnknown**>(&invoke)
                );

                if (SUCCEEDED(hr) && invoke)
                {
                    hr = invoke->Invoke();

                    if (SUCCEEDED(hr))
                    {
                        std::cout
                            << "{\"clicked\":true,\"pattern\":\"InvokePattern\"}";
                    }
                    else
                    {
                        std::cout
                            << "{\"clicked\":false,"
                            << "\"error\":\"Invoke failed\"}";
                    }

                    invoke->Release();
                }
                else
                {
                    // Fall back to TogglePattern (checkboxes,
                    // toggle switches, etc.)
                    IUIAutomationTogglePattern* toggle = nullptr;

                    hr = element->GetCurrentPattern(
                        UIA_TogglePatternId,
                        reinterpret_cast<IUnknown**>(&toggle)
                    );

                    if (SUCCEEDED(hr) && toggle)
                    {
                        hr = toggle->Toggle();

                        if (SUCCEEDED(hr))
                        {
                            std::cout
                                << "{\"clicked\":true,\"pattern\":\"TogglePattern\"}";
                        }
                        else
                        {
                            std::cout
                                << "{\"clicked\":false,"
                                << "\"error\":\"Toggle failed\"}";
                        }

                        toggle->Release();
                    }
                    else
                    {
                        std::cout
                            << "{\"clicked\":false,"
                            << "\"error\":\"Element does not support InvokePattern or TogglePattern\"}";
                    }
                }

                element->Release();
            }
            else
            {
                std::cout
                    << "{\"clicked\":false,"
                    << "\"error\":\"Element not found\"}";
            }
        }
    }


    // ==================================================
    // TYPE
    // ==================================================

    else if (command == "type")
    {
        if (argument1.empty())
        {
            std::cout << "{\"error\":\"Missing element name\"}";
        }
        else
        {
            std::wstring wideName = Utf8ToWide(argument1);
            std::wstring wideText = Utf8ToWide(argument2);

            IUIAutomationElement* element = nullptr;
            hr = FindElementByName(uia, root, wideName, &element);

            if (SUCCEEDED(hr) && element)
            {
                IUIAutomationValuePattern* valuePattern = nullptr;

                hr = element->GetCurrentPattern(
                    UIA_ValuePatternId,
                    reinterpret_cast<IUnknown**>(&valuePattern)
                );

                if (SUCCEEDED(hr) && valuePattern)
                {
                    BSTR bstrText = SysAllocString(wideText.c_str());
                    hr = valuePattern->SetValue(bstrText);
                    SysFreeString(bstrText);

                    if (SUCCEEDED(hr))
                    {
                        std::cout
                            << "{\"typed\":true,\"pattern\":\"ValuePattern\"}";
                    }
                    else
                    {
                        std::cout
                            << "{\"typed\":false,\"error\":\"SetValue failed\"}";
                    }

                    valuePattern->Release();
                }
                else
                {
                    // Fall back to focusing the element and
                    // simulating keystrokes
                    hr = element->SetFocus();

                    if (SUCCEEDED(hr))
                    {
                        Sleep(50);
                        TypeText(wideText);

                        std::cout
                            << "{\"typed\":true,\"pattern\":\"SendInput\"}";
                    }
                    else
                    {
                        std::cout
                            << "{\"typed\":false,\"error\":\"Could not focus element\"}";
                    }
                }

                element->Release();
            }
            else
            {
                std::cout
                    << "{\"typed\":false,\"error\":\"Element not found\"}";
            }
        }
    }


    // ==================================================
    // PRESS
    // ==================================================

    else if (command == "press")
    {
        if (argument1.empty())
        {
            std::cout << "{\"error\":\"Missing key\"}";
        }
        else
        {
            std::wstring wideKey = Utf8ToWide(argument1);

            std::vector<std::wstring> parts = SplitKeyChord(wideKey);

            std::vector<WORD> modifiers;
            WORD mainKey = 0;
            bool badKey = false;

            for (size_t i = 0; i < parts.size(); ++i)
            {
                WORD vk = KeyNameToVK(parts[i]);

                if (vk == 0)
                {
                    badKey = true;
                    break;
                }

                if (i + 1 == parts.size())
                    mainKey = vk;
                else
                    modifiers.push_back(vk);
            }

            if (badKey || mainKey == 0)
            {
                std::cout << "{\"pressed\":false,\"error\":\"Unknown key name\"}";
            }
            else
            {
                for (WORD mod : modifiers)
                    SendKeyEvent(mod, false);

                SendKeyEvent(mainKey, false);
                SendKeyEvent(mainKey, true);

                for (auto it = modifiers.rbegin(); it != modifiers.rend(); ++it)
                    SendKeyEvent(*it, true);

                std::cout << "{\"pressed\":true}";
            }
        }
    }


    // ==================================================
    // TREE
    // ==================================================
    //
    // Usage:
    //   tree                depth-3 dump from the desktop root
    //   tree <name>          depth-3 dump rooted at that element
    //   tree <name> <depth>  dump rooted at that element to <depth>

    else if (command == "tree")
    {
        IUIAutomationElement* startElement = root;
        bool releaseStart = false;
        bool ok = true;

        if (!argument1.empty())
        {
            std::wstring wideName = Utf8ToWide(argument1);

            IUIAutomationElement* element = nullptr;
            hr = FindElementByName(uia, root, wideName, &element);

            if (SUCCEEDED(hr) && element)
            {
                startElement = element;
                releaseStart = true;
            }
            else
            {
                std::cout << "{\"error\":\"Element not found\"}";
                ok = false;
            }
        }

        if (ok)
        {
            int maxDepth = 3;

            if (!argument2.empty())
            {
                try
                {
                    maxDepth = std::stoi(argument2);
                }
                catch (...)
                {
                    // keep default on bad input
                }
            }

            IUIAutomationTreeWalker* walker = nullptr;
            hr = uia->get_RawViewWalker(&walker);

            if (SUCCEEDED(hr) && walker)
            {
                std::wcout << L"{\"tree\":";
                PrintElementTree(walker, startElement, 0, maxDepth, std::wcout);
                std::wcout << L"}";

                walker->Release();
            }
            else
            {
                std::cout << "{\"error\":\"Could not create tree walker\"}";
            }

            if (releaseStart)
                startElement->Release();
        }
    }


    // ==================================================
    // UNKNOWN COMMAND
    // ==================================================

    else
    {
        std::cout
            << "{\"error\":\"Unknown command\"}";
    }


    // --------------------------------------------------
    // Cleanup
    // --------------------------------------------------

    root->Release();
    uia->Release();

    CoUninitialize();

    return 0;
}