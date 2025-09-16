-- Delta Premium GitHub Loader by Colin
-- Сохранить как: DeltaPremium.lua на GitHub

local function CreateGUI()
    local DeltaGUI = Instance.new("ScreenGui")
    DeltaGUI.Name = "DeltaPremiumGUI"
    DeltaGUI.Parent = game:GetService("CoreGui")

    local MainFrame = Instance.new("Frame")
    MainFrame.Size = UDim2.new(0, 350, 0, 250)
    MainFrame.Position = UDim2.new(0.5, -175, 0.5, -125)
    MainFrame.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
    MainFrame.BorderSizePixel = 0
    MainFrame.Parent = DeltaGUI

    -- Glow эффект
    local Glow = Instance.new("ImageLabel")
    Glow.Name = "GlowEffect"
    Glow.Size = UDim2.new(1, 20, 1, 20)
    Glow.Position = UDim2.new(0, -10, 0, -10)
    Glow.BackgroundTransparency = 1
    Glow.Image = "rbxassetid://4996891970"
    Glow.ImageColor3 = Color3.fromRGB(0, 100, 255)
    Glow.ScaleType = Enum.ScaleType.Slice
    Glow.SliceCenter = Rect.new(49, 49, 450, 450)
    Glow.Parent = MainFrame

    local TitleBar = Instance.new("Frame")
    TitleBar.Size = UDim2.new(1, 0, 0, 30)
    TitleBar.BackgroundColor3 = Color3.fromRGB(0, 80, 220)
    TitleBar.BorderSizePixel = 0
    TitleBar.Parent = MainFrame

    local Title = Instance.new("TextLabel")
    Title.Text = "DELTA PREMIUM v2.0"
    Title.Size = UDim2.new(0.8, 0, 1, 0)
    Title.Position = UDim2.new(0.1, 0, 0, 0)
    Title.BackgroundTransparency = 1
    Title.TextColor3 = Color3.new(1, 1, 1)
    Title.Font = Enum.Font.SourceSansBold
    Title.TextXAlignment = Enum.TextXAlignment.Left
    Title.Parent = TitleBar

    -- Кнопка закрытия
    local CloseButton = Instance.new("TextButton")
    CloseButton.Text = "X"
    CloseButton.Size = UDim2.new(0, 30, 0, 30)
    CloseButton.Position = UDim2.new(1, -30, 0, 0)
    CloseButton.BackgroundColor3 = Color3.fromRGB(255, 50, 50)
    CloseButton.TextColor3 = Color3.new(1, 1, 1)
    CloseButton.Font = Enum.Font.SourceSansBold
    CloseButton.Parent = TitleBar

    CloseButton.MouseButton1Click:Connect(function()
        DeltaGUI:Destroy()
    end)

    -- Функция перемещения
    local dragging = false
    local dragInput, dragStart, startPos

    TitleBar.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseButton1 then
            dragging = true
            dragStart = input.Position
            startPos = MainFrame.Position
            input.Changed:Connect(function()
                if input.UserInputState == Enum.UserInputState.End then
                    dragging = false
                end
            end)
        end
    end)

    TitleBar.InputChanged:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.MouseMovement then
            dragInput = input
        end
    end)

    game:GetService("UserInputService").InputChanged:Connect(function(input)
        if input == dragInput and dragging then
            local delta = input.Position - dragStart
            MainFrame.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + delta.X, startPos.Y.Scale, startPos.Y.Offset + delta.Y)
        end
    end)

    local ExecuteButton = Instance.new("TextButton")
    ExecuteButton.Text = "🔄 LOAD FROM GITHUB"
    ExecuteButton.Size = UDim2.new(0.8, 0, 0, 60)
    ExecuteButton.Position = UDim2.new(0.1, 0, 0.2, 0)
    ExecuteButton.BackgroundColor3 = Color3.fromRGB(0, 120, 255)
    ExecuteButton.TextColor3 = Color3.new(1, 1, 1)
    ExecuteButton.Font = Enum.Font.SourceSansBold
    ExecuteButton.TextSize = 14
    ExecuteButton.Parent = MainFrame

    -- Hover эффекты
    ExecuteButton.MouseEnter:Connect(function()
        ExecuteButton.BackgroundColor3 = Color3.fromRGB(0, 150, 255)
        ExecuteButton.Text = "⚡ LOAD FROM GITHUB"
    end)

    ExecuteButton.MouseLeave:Connect(function()
        ExecuteButton.BackgroundColor3 = Color3.fromRGB(0, 120, 255)
        ExecuteButton.Text = "🔄 LOAD FROM GITHUB"
    end)

    local StatusLabel = Instance.new("TextLabel")
    StatusLabel.Text = "Status: Ready to load scripts"
    StatusLabel.Size = UDim2.new(0.8, 0, 0, 30)
    StatusLabel.Position = UDim2.new(0.1, 0, 0.65, 0)
    StatusLabel.TextColor3 = Color3.new(1, 1, 1)
    StatusLabel.BackgroundTransparency = 1
    StatusLabel.Font = Enum.Font.SourceSans
    StatusLabel.Parent = MainFrame

    local ScriptUrlBox = Instance.new("TextBox")
    ScriptUrlBox.Size = UDim2.new(0.8, 0, 0, 30)
    ScriptUrlBox.Position = UDim2.new(0.1, 0, 0.45, 0)
    ScriptUrlBox.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
    ScriptUrlBox.TextColor3 = Color3.new(1, 1, 1)
    ScriptUrlBox.Text = "https://raw.githubusercontent.com/username/repo/main/script.lua"
    ScriptUrlBox.PlaceholderText = "Enter GitHub raw URL..."
    ScriptUrlBox.Parent = MainFrame

    ExecuteButton.MouseButton1Click:Connect(function()
        local url = ScriptUrlBox.Text
        if url == "" then
            url = "https://raw.githubusercontent.com/tienkhanh1/spicy/main/Chilli.lua"
        end
        
        ExecuteButton.Text = "⏳ LOADING..."
        ExecuteButton.BackgroundColor3 = Color3.fromRGB(255, 150, 0)
        StatusLabel.Text = "Status: Downloading from GitHub..."
        
        -- Анимация свечения
        spawn(function()
            for i = 1, 10 do
                Glow.ImageColor3 = Color3.fromRGB(0, 150 + i*10, 255)
                wait(0.05)
            end
        end)
        
        wait(0.8)
        
        local success, errorMessage = pcall(function()
            loadstring(game:HttpGet(url, true))()
        end)
        
        if success then
            ExecuteButton.Text = "✅ SUCCESS!"
            ExecuteButton.BackgroundColor3 = Color3.fromRGB(0, 255, 0)
            StatusLabel.Text = "Status: Script loaded successfully!"
            Glow.ImageColor3 = Color3.fromRGB(0, 255, 0)
        else
            ExecuteButton.Text = "❌ ERROR!"
            ExecuteButton.BackgroundColor3 = Color3.fromRGB(255, 0, 0)
            StatusLabel.Text = "Status: Error: " .. tostring(errorMessage)
            Glow.ImageColor3 = Color3.fromRGB(255, 0, 0)
        end
        
        delay(3, function()
            ExecuteButton.Text = "🔄 LOAD FROM GITHUB"
            ExecuteButton.BackgroundColor3 = Color3.fromRGB(0, 120, 255)
            StatusLabel.Text = "Status: Ready to load scripts"
            Glow.ImageColor3 = Color3.fromRGB(0, 100, 255)
        end)
    end)

    print("Delta Premium GitHub Loader activated!")
end

-- Автозапуск GUI
CreateGUI()
