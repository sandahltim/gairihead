/*
 * GairiHead TFT Display Controller
 *
 * Arduino Uno + 2.8" TP28017 TFT HAT (240x320)
 * Serial communication with Raspberry Pi 5
 *
 * Features:
 * - 3 display views: Conversation, Status, Debug
 * - Touch button interface
 * - Expression-to-emoji mapping
 * - Authorization level color coding
 * - JSON protocol over USB serial
 *
 * Uses MCUFRIEND_kbv library for 8-bit parallel interface
 */

#include <Adafruit_GFX.h>
#include <MCUFRIEND_kbv.h>
#include <TouchScreen.h>
#include <ArduinoJson.h>

// =============================================================================
// HARDWARE CONFIGURATION
// =============================================================================

// TFT uses 8-bit parallel interface (no CS/DC/RST defines needed)

// Touchscreen pins (2.8" TFT HAT)
#define YP A2  // Y+ (must be analog)
#define XM A3  // X- (must be analog)
#define YM 7   // Y-
#define XP 6   // X+

// Touchscreen calibration
#define TS_MINX 150
#define TS_MINY 120
#define TS_MAXX 920
#define TS_MAXY 940
#define MINPRESSURE 10
#define MAXPRESSURE 1000

// Display dimensions
#define SCREEN_WIDTH  240
#define SCREEN_HEIGHT 320

// =============================================================================
// OBJECTS
// =============================================================================

MCUFRIEND_kbv tft;  // Use MCUFRIEND for parallel interface
TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300);

// =============================================================================
// COLORS
// =============================================================================

#define COLOR_BG       0x0000  // Black
#define COLOR_TEXT     0xFFFF  // White
#define COLOR_TITLE    0x07FF  // Cyan
#define COLOR_USER     0x07E0  // Green
#define COLOR_GAIRI    0x07FF  // Cyan
#define COLOR_BUTTON   0x4208  // Dark gray
#define COLOR_AUTH_1   0x07E0  // Green (Level 1 - Tim)
#define COLOR_AUTH_2   0xFFE0  // Yellow (Level 2 - Authorized)
#define COLOR_AUTH_3   0xF800  // Red (Level 3 - Stranger)
#define COLOR_EXPR     0xFBE0  // Orange (Expression)

// =============================================================================
// DISPLAY MODES
// =============================================================================

enum DisplayView {
  VIEW_CONVERSATION,
  VIEW_STATUS,
  VIEW_DEBUG
};

DisplayView currentView = VIEW_CONVERSATION;

// =============================================================================
// TOUCH BUTTON STRUCTURE
// =============================================================================

struct TouchButton {
  int x, y, w, h;
  String action;
};

// =============================================================================
// STATE VARIABLES
// =============================================================================

// Conversation data
String userText = "";
String gairiText = "";
String expression = "idle";
String tier = "local";
float responseTime = 0.0;

// Status data
String userName = "Unknown";
int authLevel = 3;
String systemState = "idle";
float confidence = 0.0;

// Debug data
String lastTool = "none";
bool trainingLogged = false;

// Touch handling
unsigned long lastTouchTime = 0;
const unsigned long touchDebounce = 500; // ms

// Serial buffer
String serialBuffer = "";
const unsigned int maxBufferSize = 1024;

// =============================================================================
// EXPRESSION TO EMOJI MAPPING
// =============================================================================

String expressionToEmoji(String expr) {
  if (expr == "happy") return F(":)");
  if (expr == "amused") return F(":D");
  if (expr == "sarcasm") return F(";)");
  if (expr == "deadpan") return F(":|");
  if (expr == "unimpressed") return F("-_-");
  if (expr == "disapproval") return F(":/");
  if (expr == "calculating") return F("o.O");
  if (expr == "thinking") return F("...");
  if (expr == "processing") return F("(*_*)");
  if (expr == "alert") return F("!");
  if (expr == "concern") return F(":(");
  if (expr == "frustrated") return F(">:(");
  if (expr == "confused") return F("???");
  if (expr == "sheepish") return F("^_^;");
  if (expr == "pride") return F("^_^");
  if (expr == "celebration") return F("\\o/");
  if (expr == "listening") return F("<ear>");
  return F("o_o");
}

// =============================================================================
// TEXT WRAPPING UTILITY
// =============================================================================

void wrapText(String text, int x, int y, int maxWidth, int lineHeight, uint16_t color) {
  tft.setTextColor(color);
  tft.setTextSize(1);

  int cursorX = x;
  int cursorY = y;
  String word = "";

  for (unsigned int i = 0; i < text.length(); i++) {
    char c = text.charAt(i);

    if (c == ' ' || c == '\n' || i == text.length() - 1) {
      // Add last character if end of string
      if (i == text.length() - 1 && c != ' ' && c != '\n') {
        word += c;
      }

      // Measure word width
      int16_t x1, y1;
      uint16_t w, h;
      tft.getTextBounds(word.c_str(), 0, 0, &x1, &y1, &w, &h);

      // Check if word fits on current line
      if (cursorX + w > x + maxWidth) {
        // Move to next line
        cursorX = x;
        cursorY += lineHeight;

        // Check if we're past screen bottom
        if (cursorY > SCREEN_HEIGHT - lineHeight) {
          return; // Stop drawing
        }
      }

      // Draw word
      tft.setCursor(cursorX, cursorY);
      tft.print(word);
      cursorX += w + 6; // Add space width

      word = "";

      // Handle newline
      if (c == '\n') {
        cursorX = x;
        cursorY += lineHeight;
      }
    } else {
      word += c;
    }
  }
}

// =============================================================================
// BUTTON DRAWING
// =============================================================================

void drawButton(int x, int y, int w, int h, String label, uint16_t bgColor, uint16_t textColor) {
  tft.fillRoundRect(x, y, w, h, 5, bgColor);
  tft.drawRoundRect(x, y, w, h, 5, textColor);

  // Center text in button
  int16_t x1, y1;
  uint16_t tw, th;
  tft.setTextSize(1);
  tft.getTextBounds(label.c_str(), 0, 0, &x1, &y1, &tw, &th);

  tft.setCursor(x + (w - tw) / 2, y + (h - th) / 2);
  tft.setTextColor(textColor);
  tft.print(label);
}

// =============================================================================
// TOUCH DETECTION
// =============================================================================

// Touch buttons at bottom
TouchButton btnLeft = {10, 280, 70, 35, "View"};
TouchButton btnCenter = {85, 280, 70, 35, "Action"};
TouchButton btnRight = {160, 280, 70, 35, "View"};

bool isTouchInButton(TSPoint p, TouchButton btn) {
  // Map touch coordinates to screen coordinates
  int px = map(p.x, TS_MINX, TS_MAXX, 0, SCREEN_WIDTH);
  int py = map(p.y, TS_MINY, TS_MAXY, 0, SCREEN_HEIGHT);

  return (px >= btn.x && px <= btn.x + btn.w &&
          py >= btn.y && py <= btn.y + btn.h);
}

// =============================================================================
// VIEW: CONVERSATION
// =============================================================================

void drawConversationView() {
  tft.fillScreen(COLOR_BG);

  // Title
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(10, 10);
  tft.print("Conversation");

  // Expression emoji
  tft.setTextSize(3);
  tft.setTextColor(COLOR_EXPR);
  tft.setCursor(SCREEN_WIDTH - 50, 10);
  tft.print(expressionToEmoji(expression));

  // User text
  tft.setTextSize(2);
  tft.setTextColor(COLOR_USER);
  tft.setCursor(10, 45);
  tft.print("User:");

  tft.setTextSize(1);
  wrapText(userText, 10, 65, SCREEN_WIDTH - 20, 10, COLOR_TEXT);

  // Gairi text
  int gairiY = 135;
  tft.setTextSize(2);
  tft.setTextColor(COLOR_GAIRI);
  tft.setCursor(10, gairiY);
  tft.print("Gairi:");

  tft.setTextSize(1);
  wrapText(gairiText, 10, gairiY + 20, SCREEN_WIDTH - 20, 10, COLOR_TEXT);

  // Footer info
  tft.setTextSize(1);
  tft.setTextColor(COLOR_AUTH_2);
  tft.setCursor(10, 250);
  tft.print("Tier: ");
  tft.print(tier);
  tft.print("  Time: ");
  tft.print(responseTime, 2);
  tft.print("s");

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Demo", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// =============================================================================
// VIEW: STATUS
// =============================================================================

void drawStatusView() {
  tft.fillScreen(COLOR_BG);

  // Title
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(10, 10);
  tft.print("Status");

  // User info with auth level color
  uint16_t authColor = COLOR_AUTH_3;
  if (authLevel == 1) authColor = COLOR_AUTH_1;
  else if (authLevel == 2) authColor = COLOR_AUTH_2;

  tft.setTextSize(2);
  tft.setTextColor(authColor);
  tft.setCursor(10, 50);
  tft.print("User: ");
  tft.print(userName);

  tft.setTextSize(1);
  tft.setCursor(10, 75);
  tft.print("Auth Level: ");
  tft.print(authLevel);

  // System state
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 110);
  tft.print("State:");

  tft.setTextSize(1);
  tft.setCursor(10, 135);
  tft.setTextColor(COLOR_EXPR);
  tft.print(systemState);
  tft.print(" (");
  tft.print(expression);
  tft.print(")");

  // Confidence
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 170);
  tft.print("Confidence:");

  tft.setTextSize(1);
  tft.setCursor(10, 195);
  int confPercent = (int)(confidence * 100);
  tft.print(confPercent);
  tft.print("%");

  // Confidence bar
  int barWidth = (int)(200 * confidence);
  tft.drawRect(10, 210, 200, 20, COLOR_TEXT);
  tft.fillRect(11, 211, barWidth, 18, authColor);

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Guest", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// =============================================================================
// VIEW: DEBUG
// =============================================================================

void drawDebugView() {
  tft.fillScreen(COLOR_BG);

  // Title
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(10, 10);
  tft.print("Debug Info");

  // LLM Tier
  tft.setTextSize(1);
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 50);
  tft.print("LLM Tier: ");
  tft.setTextColor(tier == "local" ? COLOR_AUTH_1 : COLOR_AUTH_2);
  tft.print(tier);

  // Last tool
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 80);
  tft.print("Last Tool:");
  tft.setCursor(10, 95);
  tft.setTextColor(COLOR_EXPR);
  tft.print(lastTool);

  // Training status
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 125);
  tft.print("Training Logged: ");
  tft.setTextColor(trainingLogged ? COLOR_AUTH_1 : COLOR_AUTH_3);
  tft.print(trainingLogged ? "YES" : "NO");

  // Response time
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 155);
  tft.print("Response Time:");
  tft.setCursor(10, 170);
  tft.setTextColor(COLOR_EXPR);
  tft.print(responseTime, 3);
  tft.print(" seconds");

  // Expression
  tft.setTextColor(COLOR_TEXT);
  tft.setCursor(10, 200);
  tft.print("Expression: ");
  tft.setTextColor(COLOR_EXPR);
  tft.print(expression);
  tft.print(" ");
  tft.setTextSize(2);
  tft.print(expressionToEmoji(expression));

  // Touch buttons
  drawButton(btnLeft.x, btnLeft.y, btnLeft.w, btnLeft.h, "<", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnCenter.x, btnCenter.y, btnCenter.w, btnCenter.h, "Demo", COLOR_BUTTON, COLOR_TEXT);
  drawButton(btnRight.x, btnRight.y, btnRight.w, btnRight.h, ">", COLOR_BUTTON, COLOR_TEXT);
}

// =============================================================================
// VIEW SWITCHING
// =============================================================================

void switchView(DisplayView newView) {
  currentView = newView;

  switch (currentView) {
    case VIEW_CONVERSATION:
      drawConversationView();
      break;
    case VIEW_STATUS:
      drawStatusView();
      break;
    case VIEW_DEBUG:
      drawDebugView();
      break;
  }
}

void nextView() {
  switch (currentView) {
    case VIEW_CONVERSATION:
      switchView(VIEW_STATUS);
      break;
    case VIEW_STATUS:
      switchView(VIEW_DEBUG);
      break;
    case VIEW_DEBUG:
      switchView(VIEW_CONVERSATION);
      break;
  }
}

void previousView() {
  switch (currentView) {
    case VIEW_CONVERSATION:
      switchView(VIEW_DEBUG);
      break;
    case VIEW_STATUS:
      switchView(VIEW_CONVERSATION);
      break;
    case VIEW_DEBUG:
      switchView(VIEW_STATUS);
      break;
  }
}

// =============================================================================
// JSON MESSAGE HANDLING
// =============================================================================

void handleJsonMessage(String json) {
  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, json);

  if (error) {
    Serial.print(F("{\"error\":\"parse\",\"code\":\""));
    Serial.print(error.c_str());
    Serial.println(F("\"}"));
    return;
  }

  const char* type = doc["type"];

  if (strcmp(type, "conversation") == 0) {
    // Extract conversation data
    const char* userTextPtr = doc["user_text"];
    const char* gairiTextPtr = doc["gairi_text"];

    userText = (userTextPtr != nullptr) ? String(userTextPtr) : "";
    gairiText = (gairiTextPtr != nullptr) ? String(gairiTextPtr) : "";
    expression = doc["expression"].as<String>();
    tier = doc["tier"] | "local";
    responseTime = doc["response_time"] | 0.0;

    // Acknowledge receipt
    Serial.println(F("{\"ok\":1}"));

    // Redraw if on conversation view
    if (currentView == VIEW_CONVERSATION) {
      drawConversationView();
    }

  } else if (strcmp(type, "status") == 0) {
    userName = doc["user"].as<String>();
    authLevel = doc["level"] | 3;
    systemState = doc["state"].as<String>();
    confidence = doc["confidence"] | 0.0;
    expression = doc["expression"].as<String>();

    if (currentView == VIEW_STATUS) {
      drawStatusView();
    }

    Serial.println(F("{\"ok\":1}"));

  } else if (strcmp(type, "debug") == 0) {
    tier = doc["tier"].as<String>();
    lastTool = doc["tool"].as<String>();
    trainingLogged = doc["training_logged"] | false;
    responseTime = doc["response_time"] | 0.0;

    if (currentView == VIEW_DEBUG) {
      drawDebugView();
    }

    Serial.println(F("{\"ok\":1}"));

  } else {
    Serial.println(F("{\"error\":\"type\"}"));
  }
}

// =============================================================================
// TOUCH HANDLING
// =============================================================================

void handleTouch() {
  TSPoint p = ts.getPoint();

  // Need to reset pins for TFT after touch reading
  pinMode(XM, OUTPUT);
  pinMode(YP, OUTPUT);

  // Check if valid touch
  if (p.z < MINPRESSURE || p.z > MAXPRESSURE) {
    return;
  }

  // Debounce
  unsigned long now = millis();
  if (now - lastTouchTime < touchDebounce) {
    return;
  }
  lastTouchTime = now;

  // Check which button was pressed
  if (isTouchInButton(p, btnLeft)) {
    // Previous view
    previousView();

  } else if (isTouchInButton(p, btnRight)) {
    // Next view
    nextView();

  } else if (isTouchInButton(p, btnCenter)) {
    // Reserved for future use
  }
}

// =============================================================================
// SETUP
// =============================================================================

void setup() {
  // Initialize serial
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port
  }

  // Initialize TFT with MCUFRIEND
  uint16_t ID = tft.readID();
  tft.begin(ID);
  tft.setRotation(0);
  tft.fillScreen(COLOR_BG);

  // Welcome message
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TITLE);
  tft.setCursor(30, 140);
  tft.print(F("GairiHead"));

  delay(1000);

  // Show initial view
  switchView(VIEW_CONVERSATION);

  // Send ready signal
  Serial.println(F("{\"ok\":1}"));
}

// =============================================================================
// MAIN LOOP
// =============================================================================

void loop() {
  // Handle serial input
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      // Complete message received
      if (serialBuffer.length() > 0) {
        handleJsonMessage(serialBuffer);
        serialBuffer = "";
      }
    } else {
      // Add to buffer
      serialBuffer += c;

      // Prevent buffer overflow
      if (serialBuffer.length() >= maxBufferSize) {
        Serial.println(F("{\"error\":\"buf\"}"));
        serialBuffer = "";
      }
    }
  }

  // Handle touch input
  handleTouch();

  // Small delay to prevent overwhelming the system
  delay(50);
}
