"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, Play, Mail, CheckCircle, Activity, Timer, Target } from "lucide-react"
import { supabase } from "@/lib/supabaseClient"

export default function RunningAnalyst() {
  const [isUploaded, setIsUploaded] = useState(false)
  const [email, setEmail] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const handleFileSelect = (file: File) => {
    if (file.type.startsWith("video/")) {
      setSelectedFile(file)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setUploadError(null)
    if (selectedFile && email) {
      try {
        // Generate a unique filename
        const fileExt = selectedFile.name.split('.').pop()
        const fileName = `${Date.now()}-${Math.random().toString(36).substring(2, 8)}.${fileExt}`
        const filePath = `uploads/${fileName}`

        // Get Supabase credentials
        const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
        const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
        const bucket = 'running-form-analysis-input'
        const uploadUrl = `${supabaseUrl}/storage/v1/object/${bucket}/${filePath}`

        // Use XMLHttpRequest to track progress
        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest()
          xhr.open('POST', uploadUrl)
          xhr.setRequestHeader('Authorization', `Bearer ${supabaseAnonKey}`)
          xhr.setRequestHeader('x-upsert', 'false')

          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              setUploadProgress(Math.round((event.loaded / event.total) * 100))
            }
          }

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              setUploadProgress(100)
              setIsUploaded(true)
              resolve()
            } else {
              setUploadError('Upload failed')
              reject(new Error('Upload failed'))
            }
          }

          xhr.onerror = () => {
            setUploadError('Upload failed')
            reject(new Error('Upload failed'))
          }

          const formData = new FormData()
          formData.append('file', selectedFile)
          xhr.send(formData)
        })
      } catch (err: any) {
        setUploadError(err.message || 'Upload failed')
      }
    }
  }

  if (isUploaded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <CardTitle className="text-2xl text-green-700">Success!</CardTitle>
            <CardDescription className="text-lg">Video uploaded successfully</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">We will send you a detailed running analysis to:</p>
            <div className="bg-muted p-3 rounded-lg">
              <p className="font-medium">{email}</p>
            </div>
            <p className="text-sm text-muted-foreground">
              Our experts will analyze your running form, pace, and technique. You'll receive your personalized report
              within 24-48 hours.
            </p>
            <Button
              onClick={() => {
                setIsUploaded(false)
                setSelectedFile(null)
                setEmail("")
              }}
              variant="outline"
              className="w-full"
            >
              Upload Another Video
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="bg-blue-600 p-3 rounded-full">
              <Activity className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-4">Running Video Analysis</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
            Upload your running video and get professional analysis to improve your form, prevent injuries, and enhance
            your performance.
          </p>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Timer className="w-8 h-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Quick Analysis</h3>
              <p className="text-sm text-gray-600">Get your detailed report within 24-48 hours</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Target className="w-8 h-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Expert Insights</h3>
              <p className="text-sm text-gray-600">Professional analysis from certified running coaches</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <Play className="w-8 h-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Video Breakdown</h3>
              <p className="text-sm text-gray-600">Frame-by-frame analysis of your running technique</p>
            </div>
          </div>
        </div>

        {/* Upload Form */}
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Upload Your Running Video</CardTitle>
            <CardDescription className="text-center">
              Upload a video of your running form for professional analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Upload Area */}
              <div className="space-y-2">
                <Label>Running Video</Label>
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragOver
                      ? "border-blue-500 bg-blue-50"
                      : selectedFile
                        ? "border-green-500 bg-green-50"
                        : "border-gray-300 hover:border-gray-400"
                  }`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                >
                  {selectedFile ? (
                    <div className="space-y-2">
                      <CheckCircle className="w-12 h-12 text-green-600 mx-auto" />
                      <p className="font-medium text-green-700">{selectedFile.name}</p>
                      <p className="text-sm text-green-600">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                      <Button type="button" variant="outline" size="sm" onClick={() => setSelectedFile(null)}>
                        Remove
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                      <div>
                        <p className="text-lg font-medium">Drop your video here</p>
                        <p className="text-gray-500">or click to browse</p>
                      </div>
                      <input
                        type="file"
                        accept="video/*"
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) handleFileSelect(file)
                        }}
                        className="hidden"
                        id="video-upload"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => document.getElementById("video-upload")?.click()}
                      >
                        Choose File
                      </Button>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500">Supported formats: MP4, MOV, AVI. Maximum file size: 500MB</p>
              </div>

              {/* Email Input */}
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="your.email@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500">We'll send your detailed analysis report to this email address</p>
              </div>

              {/* Progress Bar */}
              {uploadProgress !== null && (
                <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                  <div className="text-xs text-gray-600 mt-1 text-right">{uploadProgress}%</div>
                </div>
              )}

              {/* Error Message */}
              {uploadError && (
                <div className="text-red-600 text-sm mb-2">{uploadError}</div>
              )}

              {/* Submit Button */}
              <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={!selectedFile || !email || uploadProgress !== null}>
                Upload Video & Get Analysis
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Additional Info */}
        <div className="max-w-2xl mx-auto mt-8 text-center">
          <p className="text-sm text-gray-600">
            Your video will be analyzed by certified running coaches and biomechanics experts. We'll provide insights on
            your stride, posture, cadence, and recommendations for improvement.
          </p>
        </div>
      </div>
    </div>
  )
}
