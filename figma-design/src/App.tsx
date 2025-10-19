import {
  Mic,
  Headphones,
  Video,
  FileVideo,
  Link,
  Image,
  Volume2,
  ChevronRight,
  Briefcase,
  Home,
  FileText,
  User,
  Menu,
  Square,
} from "lucide-react";
import { Badge } from "./components/ui/badge";

export default function App() {
  const features = [
    {
      id: 1,
      icon: Mic,
      iconBg: "bg-green-500",
      title: "实时语音转文字",
      description: "实时录音同步生成文字",
      badge: "高级功能",
      badgeVariant: "default" as const,
    },
    {
      id: 2,
      icon: Headphones,
      iconBg: "bg-blue-500",
      title: "音频转文字",
      description: "请将音频文件发送至微信文件传输助手",
      badge: null,
    },
    {
      id: 3,
      icon: Video,
      iconBg: "bg-purple-500",
      title: "视频转文字",
      description: "上传视频转换文字",
      badge: null,
    },
    {
      id: 4,
      icon: FileVideo,
      iconBg: "bg-blue-400",
      title: "视频写文案提取",
      description: "转发视频号视频提取文字",
      badge: "新",
      badgeVariant: "destructive" as const,
    },
  ];

  const bottomFeatures = [
    {
      id: 5,
      icon: Link,
      iconBg: "bg-orange-500",
      title: "链接转文字",
      description: "从链接提",
    },
    {
      id: 6,
      icon: Image,
      iconBg: "bg-cyan-400",
      title: "图片转文字",
      description: "上传图片",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-blue-200 to-cyan-200 flex flex-col">
      {/* Status Bar */}
      <div className="px-6 py-3 flex items-center justify-between text-gray-700">
        <div>2:30</div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-3 border border-gray-700 rounded-sm relative">
            <div className="absolute inset-0.5 bg-gray-700"></div>
          </div>
        </div>
      </div>

      {/* Header Icons */}
      <div className="px-6 flex justify-end gap-4 mb-4">
        <button className="w-8 h-8 rounded-full bg-white/40 flex items-center justify-center">
          <div className="flex gap-0.5">
            <div className="w-1 h-1 rounded-full bg-gray-700"></div>
            <div className="w-1 h-1 rounded-full bg-gray-700"></div>
            <div className="w-1 h-1 rounded-full bg-gray-700"></div>
          </div>
        </button>
        <button className="w-8 h-8 rounded-full bg-white/40 flex items-center justify-center">
          <div className="w-5 h-5 rounded-full border-2 border-gray-700 relative">
            <div className="absolute inset-1 rounded-full border-2 border-gray-700"></div>
          </div>
        </button>
      </div>

      {/* Title */}
      <div className="text-center mb-6">
        <h1 className="text-blue-600 text-2xl">
          AI语音视频工具
        </h1>
      </div>

      {/* Info Banner */}
      <div className="px-6 mb-4">
        <div className="bg-yellow-100 rounded-full px-4 py-3 flex items-center gap-3">
          <Volume2 className="w-5 h-5 text-orange-500 flex-shrink-0" />
          <p className="text-gray-700 text-sm">
            本工具，升级套餐解锁更多权限
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 px-6 pb-32 space-y-4">
        {/* Feature Cards */}
        {features.map((feature) => (
          <div
            key={feature.id}
            className="bg-white/90 backdrop-blur-sm rounded-3xl p-4 flex items-center gap-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          >
            <div
              className={`${feature.iconBg} w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0`}
            >
              <feature.icon className="w-7 h-7 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-gray-900">
                  {feature.title}
                </h3>
                {feature.badge && (
                  <Badge
                    variant={
                      feature.badgeVariant || "secondary"
                    }
                    className="text-xs px-2 py-0"
                  >
                    {feature.badge}
                  </Badge>
                )}
              </div>
              <p className="text-gray-500 text-sm">
                {feature.description}
              </p>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
          </div>
        ))}

        {/* Bottom Feature Grid */}
        <div className="grid grid-cols-2 gap-4">
          {bottomFeatures.map((feature) => (
            <div
              key={feature.id}
              className="bg-white/90 backdrop-blur-sm rounded-3xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            >
              <div
                className={`${feature.iconBg} w-12 h-12 rounded-2xl flex items-center justify-center mb-3`}
              >
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-gray-900 mb-1">
                {feature.title}
              </h3>
              <div className="flex items-center gap-1 text-gray-500 text-sm">
                <span>{feature.description}</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>

        {/* CTA Button */}
        <div className="pt-4">
          <button className="w-full bg-gradient-to-r from-green-400 to-cyan-400 rounded-full py-4 px-6 flex items-center justify-between shadow-lg hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-3">
              <Briefcase className="w-6 h-6 text-white" />
              <span className="text-white">
                超全工具包！神器汇总！
              </span>
            </div>
            <div className="bg-cyan-300 rounded-full w-12 h-12 flex items-center justify-center">
              <span className="text-white">GO</span>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="text-center pt-4">
          <p className="text-gray-500 text-xs">
            ©河南省云助手信息科技有限公司
          </p>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-12 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-gray-200">
        <div className="flex items-center justify-around py-3">
          <button className="flex flex-col items-center gap-1">
            <Home className="w-6 h-6 text-blue-500" />
            <span className="text-blue-500 text-xs">
              语音转文字
            </span>
          </button>
          <button className="flex flex-col items-center gap-1">
            <FileText className="w-6 h-6 text-gray-400" />
            <span className="text-gray-400 text-xs">
              识别记录
            </span>
          </button>
          <button className="flex flex-col items-center gap-1">
            <User className="w-6 h-6 text-gray-400" />
            <span className="text-gray-400 text-xs">我的</span>
          </button>
        </div>
      </div>

      {/* Android Navigation Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-sm h-12 flex items-center justify-around">
        <button>
          <Menu className="w-6 h-6 text-gray-600" />
        </button>
        <button>
          <Square className="w-5 h-5 text-gray-600" />
        </button>
        <button>
          <ChevronRight className="w-6 h-6 text-gray-600 rotate-180" />
        </button>
      </div>
    </div>
  );
}