-- Premium Roblox Menu by Colin
local Players = game:GetService("Players")
local LocalPlayer = Players.LocalPlayer
local Mouse = LocalPlayer:GetMouse()
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

-- Настройки
local Settings = {
    Menu = {
        Visible = false,
        Key = Enum.KeyCode.RightShift
    },
    SilentAim = {
        Enabled = false,
        FOV = 50,
        TeamCheck = true,
        VisibleCheck = true
    },
    ESP = {
        Enabled = false,
        Boxes = true,
        Names = true,
        Distance = true
    },
    AirJump = {
        Enabled = false
    }
}

-- Создание GUI
local ScreenGui = Instance.new("ScreenGui")
ScreenGui.Name = "PremiumMenu"
ScreenGui.Parent = game:GetService("CoreGui")

local MainFrame = Instance.new("Frame")
MainFrame.Size = UDim2.new(0, 300, 0, 350)
MainFrame.Position = UDim2.new(0.5, -150, 0.5, -175)
MainFrame.BackgroundColor3 = Color3.fromRGB(25, 25, 25)
MainFrame.BorderSizePixel = 0
MainFrame.Visible = false
MainFrame.Parent = ScreenGui

-- Glow эффект
local Glow = Instance.new("ImageLabel")
Glow.Size = UDim2.new(1, 20, 1, 20)
Glow.Position = UDim2.new(0, -10, 0, -10)
Glow.BackgroundTransparency = 1
Glow.Image = "rbxassetid://4996891970"
Glow.ImageColor3 = Color3.fromRGB(0, 100, 255)
Glow.ScaleType = Enum.ScaleType.Slice
Glow.SliceCenter = Rect.new(49, 49, 450, 450)
Glow.Parent = MainFrame

-- Title Bar
local TitleBar = Instance.new("Frame")
TitleBar.Size = UDim2.new(1, 0, 0, 30)
TitleBar.BackgroundColor3 = Color3.fromRGB(0, 80, 220)
TitleBar.BorderSizePixel = 0
TitleBar.Parent = MainFrame

local Title = Instance.new("TextLabel")
Title.Text = "PREMIUM MENU V2.0"
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

UserInputService.InputChanged:Connect(function(input)
    if input == dragInput and dragging then
        local delta = input.Position - dragStart
        MainFrame.Position = UDim2.new(startPos.X.Scale, startPos.X.Offset + delta.X, startPos.Y.Scale, startPos.Y.Offset + delta.Y)
    end
end)

CloseButton.MouseButton1Click:Connect(function()
    Settings.Menu.Visible = false
    MainFrame.Visible = false
end)

-- Функции меню
local function CreateToggle(name, yPos, settingTable, settingKey, callback)
    local frame = Instance.new("Frame")
    frame.Size = UDim2.new(0.8, 0, 0, 30)
    frame.Position = UDim2.new(0.1, 0, 0, yPos)
    frame.BackgroundTransparency = 1
    frame.Parent = MainFrame

    local label = Instance.new("TextLabel")
    label.Text = name
    label.Size = UDim2.new(0.7, 0, 1, 0)
    label.TextColor3 = Color3.new(1, 1, 1)
    label.BackgroundTransparency = 1
    label.TextXAlignment = Enum.TextXAlignment.Left
    label.Parent = frame

    local toggle = Instance.new("TextButton")
    toggle.Size = UDim2.new(0.3, 0, 1, 0)
    toggle.Position = UDim2.new(0.7, 0, 0, 0)
    toggle.Text = "OFF"
    toggle.BackgroundColor3 = Color3.fromRGB(255, 50, 50)
    toggle.Parent = frame

    toggle.MouseButton1Click:Connect(function()
        local newState = not Settings[settingTable][settingKey]
        Settings[settingTable][settingKey] = newState
        toggle.Text = newState and "ON" or "OFF"
        toggle.BackgroundColor3 = newState and Color3.fromRGB(50, 255, 50) or Color3.fromRGB(255, 50, 50)
        
        if callback then
            callback(newState)
        end
    end)
    
    return toggle
end

-- Создание переключателей
CreateToggle("Silent Aim", 50, "SilentAim", "Enabled")
CreateToggle("ESP", 90, "ESP", "Enabled")
CreateToggle("Air Jump", 130, "AirJump", "Enabled")

-- FOV Slider
local FOVFrame = Instance.new("Frame")
FOVFrame.Size = UDim2.new(0.8, 0, 0, 40)
FOVFrame.Position = UDim2.new(0.1, 0, 0, 170)
FOVFrame.BackgroundTransparency = 1
FOVFrame.Parent = MainFrame

local FOVLabel = Instance.new("TextLabel")
FOVLabel.Text = "Aim FOV: " .. Settings.SilentAim.FOV
FOVLabel.Size = UDim2.new(1, 0, 0, 20)
FOVLabel.TextColor3 = Color3.new(1, 1, 1)
FOVLabel.BackgroundTransparency = 1
FOVLabel.Parent = FOVFrame

local FOVSlider = Instance.new("Frame")
FOVSlider.Size = UDim2.new(1, 0, 0, 10)
FOVSlider.Position = UDim2.new(0, 0, 0, 25)
FOVSlider.BackgroundColor3 = Color3.fromRGB(60, 60, 60)
FOVSlider.BorderSizePixel = 0
FOVSlider.Parent = FOVFrame

local FOVFill = Instance.new("Frame")
FOVFill.Size = UDim2.new(Settings.SilentAim.FOV / 100, 0, 1, 0)
FOVFill.BackgroundColor3 = Color3.fromRGB(0, 150, 255)
FOVFill.BorderSizePixel = 0
FOVFill.Parent = FOVSlider

FOVSlider.InputBegan:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1 then
        local connection
        connection = RunService.RenderStepped:Connect(function()
            local mousePos = UserInputService:GetMouseLocation()
            local sliderPos = FOVSlider.AbsolutePosition
            local sliderSize = FOVSlider.AbsoluteSize
            local relativeX = math.clamp((mousePos.X - sliderPos.X) / sliderSize.X, 0, 1)
            
            Settings.SilentAim.FOV = math.floor(relativeX * 100)
            FOVLabel.Text = "Aim FOV: " .. Settings.SilentAim.FOV
            FOVFill.Size = UDim2.new(relativeX, 0, 1, 0)
        end)
        
        input.Changed:Connect(function()
            if input.UserInputState == Enum.UserInputState.End then
                connection:Disconnect()
            end
        end)
    end
end)

-- Silent Aim функция
local function GetClosestPlayer()
    local closestPlayer = nil
    local shortestDistance = Settings.SilentAim.FOV
    
    for _, player in pairs(Players:GetPlayers()) do
        if player ~= LocalPlayer and player.Character then
            local humanoid = player.Character:FindFirstChild("Humanoid")
            local head = player.Character:FindFirstChild("Head")
            
            if humanoid and humanoid.Health > 0 and head then
                if Settings.SilentAim.TeamCheck and player.Team == LocalPlayer.Team then
                    continue
                end
                
                local screenPos, visible = workspace.CurrentCamera:WorldToViewportPoint(head.Position)
                if Settings.SilentAim.VisibleCheck and not visible then
                    continue
                end
                
                local mousePos = Vector2.new(Mouse.X, Mouse.Y)
                local playerPos = Vector2.new(screenPos.X, screenPos.Y)
                local distance = (mousePos - playerPos).Magnitude
                
                if distance < shortestDistance then
                    shortestDistance = distance
                    closestPlayer = player
                end
            end
        end
    end
    
    return closestPlayer
end

-- ESP функция
local ESPObjects = {}
local function UpdateESP()
    for _, obj in pairs(ESPObjects) do
        if obj then
            obj:Destroy()
        end
    end
    ESPObjects = {}
    
    if not Settings.ESP.Enabled then return end
    
    for _, player in pairs(Players:GetPlayers()) do
        if player ~= LocalPlayer and player.Character then
            local humanoid = player.Character:FindFirstChild("Humanoid")
            local head = player.Character:FindFirstChild("Head")
            
            if humanoid and humanoid.Health > 0 and head then
                -- ESP Box
                if Settings.ESP.Boxes then
                    local box = Instance.new("BoxHandleAdornment")
                    box.Size = Vector3.new(4, 6, 1)
                    box.Adornee = head
                    box.AlwaysOnTop = true
                    box.ZIndex = 5
                    box.Color3 = player.Team == LocalPlayer.Team and Color3.fromRGB(0, 255, 0) or Color3.fromRGB(255, 0, 0)
                    box.Transparency = 0.5
                    box.Parent = head
                    table.insert(ESPObjects, box)
                end
                
                -- ESP Name
                if Settings.ESP.Names then
                    local billboard = Instance.new("BillboardGui")
                    billboard.Size = UDim2.new(0, 100, 0, 40)
                    billboard.Adornee = head
                    billboard.AlwaysOnTop = true
                    billboard.ExtentsOffset = Vector3.new(0, 3, 0)
                    
                    local nameLabel = Instance.new("TextLabel")
                    nameLabel.Text = player.Name
                    nameLabel.Size = UDim2.new(1, 0, 0.5, 0)
                    nameLabel.TextColor3 = Color3.new(1, 1, 1)
                    nameLabel.BackgroundTransparency = 1
                    nameLabel.Parent = billboard
                    
                    if Settings.ESP.Distance then
                        local distanceLabel = Instance.new("TextLabel")
                        distanceLabel.Text = math.floor((LocalPlayer.Character.Head.Position - head.Position).Magnitude) .. " studs"
                        distanceLabel.Size = UDim2.new(1, 0, 0.5, 0)
                        distanceLabel.Position = UDim2.new(0, 0, 0.5, 0)
                        distanceLabel.TextColor3 = Color3.new(1, 1, 1)
                        distanceLabel.BackgroundTransparency = 1
                        distanceLabel.Parent = billboard
                    end
                    
                    billboard.Parent = head
                    table.insert(ESPObjects, billboard)
                end
            end
        end
    end
end

-- Air Jump функция
UserInputService.JumpRequest:Connect(function()
    if Settings.AirJump.Enabled and LocalPlayer.Character then
        local humanoid = LocalPlayer.Character:FindFirstChild("Humanoid")
        if humanoid then
            humanoid:ChangeState(Enum.HumanoidStateType.Jumping)
        end
    end
end)

-- Основные циклы
RunService.RenderStepped:Connect(function()
    -- Silent Aim
    if Settings.SilentAim.Enabled then
        local target = GetClosestPlayer()
        if target and target.Character and target.Character:FindFirstChild("Head") then
            Mouse.Target = target.Character.Head
        end
    end
    
    -- ESP
    UpdateESP()
end)

-- Переключение меню
UserInputService.InputBegan:Connect(function(input)
    if input.KeyCode == Settings.Menu.Key then
        Settings.Menu.Visible = not Settings.Menu.Visible
        MainFrame.Visible = Settings.Menu.Visible
        Glow.ImageColor3 = Settings.Menu.Visible and Color3.fromRGB(0, 150, 255) or Color3.fromRGB(0, 100, 255)
    end
end)

print("Premium Menu loaded! Press RightShift to open/close")
