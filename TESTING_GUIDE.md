# Quick Test Instructions for AI Traffic Control System

## How the System Works:

### 1. **Initial State**
- All traffic lights start RED
- System waits for you to upload images/videos and start

### 2. **Traffic Light Logic**
- Roads are sorted by vehicle count (highest traffic first)
- Only ONE light is GREEN at a time
- All other lights stay RED while waiting
- Timer shows countdown for the current green light

### 3. **Timer Calculation**
- Base time: 10 seconds
- Additional: 2 seconds per vehicle detected
- Maximum: 60 seconds
- Example: 5 vehicles = 10 + (5 × 2) = 20 seconds

### 4. **Road Priority**
- **High Traffic**: Gets green light first with longer duration
- **Medium Traffic**: Gets green light after high traffic roads
- **No Traffic (0 vehicles)**: Stays RED, skipped entirely

### 5. **System Flow**
```
Start → Highest Traffic Road turns GREEN (others RED)
     → Timer counts down
     → When timer reaches 0, that road turns RED
     → Next highest traffic road turns GREEN
     → Repeat cycle
```

## Testing Steps:

1. **Go to**: http://127.0.0.1:5000

2. **Click**: "Get Started"

3. **Configure**: 
   - Select number of lights (e.g., 3)
   - Upload different images for each traffic light
   - Use images from the 'images' folder if available

4. **Click**: "Analyze Traffic" 
   - System will count vehicles in each image
   - You'll see vehicle counts displayed

5. **Click**: "Start Traffic Lights"
   - Monitor page opens
   - All lights start RED

6. **Click**: "▶ Start System"
   - Road with MOST vehicles turns GREEN first
   - Timer starts counting down
   - Other roads stay RED
   - When timer hits 0, next road gets green

7. **Watch**:
   - Lights change based on vehicle density
   - Timers count down in real-time
   - Roads with 0 vehicles stay red

## Expected Behavior:

**Example with 3 roads:**
- Road 1: 10 vehicles → Timer: 30 seconds
- Road 2: 5 vehicles → Timer: 20 seconds  
- Road 3: 0 vehicles → Stays RED

**Sequence:**
1. Road 1 GREEN (30s) | Road 2 RED | Road 3 RED
2. Road 2 GREEN (20s) | Road 1 RED | Road 3 RED
3. Road 3 SKIPPED (0 vehicles)
4. Cycle repeats from Road 1

## Notes:
- Only one road is green at any time
- Timer shows remaining seconds for green light
- Vehicle count displays detected vehicles
- System Status shows "Active" when running
- Click "⏹ Stop System" to halt traffic control
