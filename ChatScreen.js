/*
ChatScreen.js —— 聊天页面(现代化图标 + 微信式语音消息)

改动说明:
1. 图标换成 @expo/vector-icons(Expo项目自带,不用额外安装),
   不再用emoji,看起来更像正规App。
2. 语音消息改成微信的交互方式:
   - 按住麦克风图标开始录音,松开发送
   - 发送后立即变成一条"语音气泡"(显示时长),不是文字
   - 她的回复也是一条可点击播放的语音气泡,不再是自动念出来
   - 双方的语音气泡都点一下才播放,更贴近真实聊天软件的感觉
*/
import { useEffect } from "react";
import React, { useState, useRef } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Image,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import {
  useAudioRecorder,
  RecordingPresets,
  AudioModule,
  setAudioModeAsync,
  createAudioPlayer,
} from "expo-av";

const BACKEND_URL = "http://47.79.34.220:8000";
const USER_ID = "me";
const ACCENT = "#FF8FA3";

export default function ChatScreen({ navigation }) {
  const [messages, setMessages] = useState([
    { id: "welcome", role: "assistant", type: "text", text: "诶,你可算来啦~ 找我干嘛呀?" },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [pendingImage, setPendingImage] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const listRef = useRef(null);
  const soundRef = useRef(null);
  // expo-audio要求录音器在组件顶层用hook声明,不能像旧的expo-av那样临时创建
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  useEffect(() => {
  const t = (url) =>
    Promise.race([
      fetch(url).then((r) => "通 " + r.status),
      new Promise((_, rej) => setTimeout(() => rej(new Error("超时")), 8000)),
    ]).catch((e) => "失败 " + e.message);
  Promise.all([t("http://neverssl.com"), t("http://47.79.34.220:8000/health")]).then(
    ([a, b]) => alert("测试站: " + a + "\n我的后端: " + b)
  );
}, []);
  const pickImage = async (fromCamera) => {
    const permission = fromCamera
      ? await ImagePicker.requestCameraPermissionsAsync()
      : await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      alert("需要相机/相册权限才能发照片哦");
      return;
    }
    const result = fromCamera
      ? await ImagePicker.launchCameraAsync({ base64: true, quality: 0.5 })
      : await ImagePicker.launchImageLibraryAsync({ base64: true, quality: 0.5 });
    if (!result.canceled && result.assets && result.assets[0]) {
      const asset = result.assets[0];
      setPendingImage({ base64: asset.base64, mime: "image/jpeg", uri: asset.uri });
    }
  };

  const playAudio = async (base64Audio) => {
    try {
      // 切换到新语音前,先释放上一个播放器,避免声音叠在一起
      if (soundRef.current) {
        soundRef.current.remove();
      }
      const player = createAudioPlayer({ uri: `data:audio/mp3;base64,${base64Audio}` });
      soundRef.current = player;
      player.play();
    } catch (err) {
      console.log("播放失败:", err.message);
    }
  };

  const startRecording = async () => {
    try {
      const permission = await AudioModule.requestRecordingPermissionsAsync();
      if (!permission.granted) {
        alert("需要麦克风权限才能发语音哦");
        return;
      }
      await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
      await audioRecorder.prepareToRecordAsync();
      audioRecorder.record();
      setIsRecording(true);
    } catch (err) {
      console.log("录音启动失败:", err.message);
    }
  };

  const stopRecordingAndSend = async () => {
    setIsRecording(false);
    try {
      await audioRecorder.stop();
      const uri = audioRecorder.uri; // expo-audio录完后,文件路径直接挂在recorder对象上

      const response = await fetch(uri);
      const blob = await response.blob();
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Audio = reader.result.split(",")[1];
        await sendVoiceMessage(base64Audio);
      };
      reader.readAsDataURL(blob);
    } catch (err) {
      console.log("停止录音失败:", err.message);
    }
  };

  const sendVoiceMessage = async (base64Audio) => {
    const voiceMsgId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { id: voiceMsgId, role: "user", type: "voice", audioBase64: base64Audio },
    ]);
    setSending(true);

    try {
      const res = await fetch(`${BACKEND_URL}/voice-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, audio_base64: base64Audio }),
      });
      if (!res.ok) throw new Error(`后端返回错误状态: ${res.status}`);
      const data = await res.json();

      setMessages((prev) =>
        prev.map((m) => (m.id === voiceMsgId ? { ...m, recognizedText: data.user_text } : m))
      );

      setMessages((prev) => [
        ...prev,
        {
          id: voiceMsgId + "-r",
          role: "assistant",
          type: "voice",
          text: data.reply_text,
          audioBase64: data.reply_audio_base64,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: voiceMsgId + "-err",
          role: "assistant",
          type: "text",
          text: `(语音消息发送失败: ${err.message})`,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    if ((!text && !pendingImage) || sending) return;

    const userMsg = {
      id: Date.now().toString(),
      role: "user",
      type: "text",
      text: text || "(发了一张照片)",
      imageUri: pendingImage?.uri,
    };
    setMessages((prev) => [...prev, userMsg]);

    const imageToSend = pendingImage;
    setInput("");
    setPendingImage(null);
    setSending(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: USER_ID,
          message: text || "看看这张照片",
          image_base64: imageToSend?.base64 || null,
          image_mime: imageToSend?.mime || null,
        }),
      });
      if (!res.ok) throw new Error(`后端返回错误状态: ${res.status}`);
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString() + "-r", role: "assistant", type: "text", text: data.reply },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString() + "-err",
          role: "assistant",
          type: "text",
          text: `(连接失败: ${err.message}。检查一下后端是不是启动了,IP地址对不对)`,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const renderItem = ({ item }) => {
    const isUser = item.role === "user";

    if (item.type === "voice") {
      return (
        <TouchableOpacity
          style={[styles.bubble, styles.voiceBubble, isUser ? styles.userBubble : styles.aiBubble]}
          onPress={() => playAudio(item.audioBase64)}
        >
          <Ionicons name="play" size={16} color={isUser ? "#fff" : ACCENT} />
          <View style={styles.voiceBars}>
            <View style={[styles.voiceBar, { height: 10 }]} />
            <View style={[styles.voiceBar, { height: 16 }]} />
            <View style={[styles.voiceBar, { height: 8 }]} />
          </View>
          {(item.recognizedText || item.text) && (
            <Text style={[styles.voiceSubText, isUser ? styles.userText : styles.aiText]}>
              {item.recognizedText || item.text}
            </Text>
          )}
        </TouchableOpacity>
      );
    }

    return (
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
        {item.imageUri && <Image source={{ uri: item.imageUri }} style={styles.messageImage} />}
        <Text style={isUser ? styles.userText : styles.aiText}>{item.text}</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <TouchableOpacity style={styles.header} onPress={() => navigation.navigate("Profile")}>
          <Image source={require("../assets/avatar.png")} style={styles.headerAvatar} />
          <Text style={styles.headerText}>爱弥斯</Text>
        </TouchableOpacity>

        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        />

        {pendingImage && (
          <View style={styles.previewRow}>
            <Image source={{ uri: pendingImage.uri }} style={styles.previewImage} />
            <TouchableOpacity onPress={() => setPendingImage(null)}>
              <Ionicons name="close-circle" size={22} color="#999" />
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.inputRow}>
          <TouchableOpacity style={styles.iconBtn} onPress={() => pickImage(true)}>
            <Ionicons name="camera-outline" size={24} color="#777" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.iconBtn} onPress={() => pickImage(false)}>
            <Ionicons name="image-outline" size={24} color="#777" />
          </TouchableOpacity>

          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="说点什么..."
            onSubmitEditing={sendMessage}
          />

          {input.trim().length > 0 ? (
            <TouchableOpacity style={styles.sendBtn} onPress={sendMessage} disabled={sending}>
              <Ionicons name="send" size={18} color="#fff" />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.micBtn, isRecording && styles.micBtnActive]}
              onPressIn={startRecording}
              onPressOut={stopRecordingAndSend}
            >
              <Ionicons name="mic" size={20} color="#fff" />
            </TouchableOpacity>
          )}
        </View>
        {isRecording && <Text style={styles.recordingHint}>松开发送</Text>}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#FFF5F7" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    gap: 8,
  },
  headerAvatar: { width: 32, height: 32, borderRadius: 16 },
  headerText: { fontSize: 20, fontWeight: "600", color: "#333" },
  list: { padding: 12, gap: 8 },
  bubble: {
    maxWidth: "75%",
    borderRadius: 16,
    paddingVertical: 8,
    paddingHorizontal: 14,
    marginVertical: 4,
  },
  userBubble: { alignSelf: "flex-end", backgroundColor: ACCENT },
  aiBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#F0DDE2",
  },
  userText: { color: "#fff", fontSize: 15 },
  aiText: { color: "#333", fontSize: 15 },
  messageImage: { width: 180, height: 180, borderRadius: 10, marginBottom: 6 },
  voiceBubble: { flexDirection: "row", alignItems: "center", gap: 8, minWidth: 90 },
  voiceBars: { flexDirection: "row", alignItems: "flex-end", gap: 2, height: 18 },
  voiceBar: { width: 3, borderRadius: 2, backgroundColor: "#ccc" },
  voiceSubText: { fontSize: 12, marginLeft: 4, opacity: 0.8 },
  previewRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 10,
    backgroundColor: "#fff",
  },
  previewImage: { width: 50, height: 50, borderRadius: 8 },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 10,
    borderTopWidth: 1,
    borderTopColor: "#eee",
    backgroundColor: "#fff",
    gap: 4,
  },
  iconBtn: { padding: 6 },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: 4,
  },
  sendBtn: {
    backgroundColor: ACCENT,
    borderRadius: 18,
    width: 36,
    height: 36,
    alignItems: "center",
    justifyContent: "center",
  },
  micBtn: {
    backgroundColor: ACCENT,
    borderRadius: 18,
    width: 36,
    height: 36,
    alignItems: "center",
    justifyContent: "center",
  },
  micBtnActive: { backgroundColor: "#E85D75", transform: [{ scale: 1.15 }] },
  recordingHint: { textAlign: "center", fontSize: 12, color: "#999", paddingBottom: 6 },
});