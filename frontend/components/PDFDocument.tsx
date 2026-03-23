"use client";

import React from 'react';
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Image,
  Font,
} from '@react-pdf/renderer';
import { Job } from '@/lib/types';

// Register multi-language fonts (static TTF only, @react-pdf doesn't support variable fonts)
Font.register({
  family: 'Noto Sans',
  fonts: [
    { src: '/fonts/NotoSans-Regular.ttf', fontWeight: 'normal' },
    { src: '/fonts/NotoSans-Bold.ttf', fontWeight: 'bold' },
  ]
});

Font.register({
  family: 'Noto Sans JP',
  src: '/fonts/NotoSansJP-Regular.ttf',
});

// Use Noto Sans as default with fallbacks for CJK languages
// Noto Sans supports Latin, Cyrillic, Greek, and most other scripts
// For CJK content, we'll detect and apply specific fonts

// Helper function to detect if text contains Japanese characters
const detectScriptType = (text: string): string => {
  if (!text) return 'Noto Sans';
  
  // Japanese (Hiragana, Katakana, Kanji)
  // Check for Japanese first as it's most common for CJK content
  if (/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(text)) {
    return 'Noto Sans JP';
  }
  
  // For all other languages (Korean, Chinese, Arabic, etc.), 
  // use Noto Sans which has good coverage for most scripts
  // @react-pdf/renderer doesn't support all Noto variants well
  return 'Noto Sans';
};

// Custom Text component that auto-detects font
const SmartText = ({ style, children, ...props }: any) => {
  const textContent = typeof children === 'string' ? children : '';
  const detectedFont = detectScriptType(textContent);
  
  const combinedStyle = Array.isArray(style) 
    ? [...style, { fontFamily: detectedFont }]
    : { ...style, fontFamily: detectedFont };
  
  return <Text style={combinedStyle} {...props}>{children}</Text>;
};

// Create styles that match the web page
const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontFamily: 'Noto Sans',
    fontSize: 10,
    lineHeight: 1.5,
    backgroundColor: '#F9FAFB',
    color: '#000000',
  },
  header: {
    marginBottom: 24,
    paddingBottom: 16,
    borderBottom: '2 solid #E5E7EB',
  },
  reportTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000000',
    marginBottom: 8,
  },
  reportSubtitle: {
    fontSize: 10,
    color: '#666666',
  },
  
  // Job Info Section
  jobInfoBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  jobInfoRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  jobInfoLabel: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#666666',
    width: 80,
  },
  jobInfoValue: {
    fontSize: 9,
    color: '#000000',
    flex: 1,
  },
  
  // Section styles
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000000',
    marginBottom: 12,
  },
  
  // Video Information (YouTube Metadata)
  videoInfoBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 20,
  },
  thumbnail: {
    width: '100%',
    height: 280,
    objectFit: 'cover',
  },
  videoInfoContent: {
    padding: 16,
  },
  videoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#000000',
    marginBottom: 12,
  },
  channelInfo: {
    fontSize: 9,
    color: '#666666',
    marginBottom: 8,
  },
  publishedInfo: {
    fontSize: 9,
    color: '#666666',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTop: '1 solid #E5E7EB',
    marginBottom: 12,
  },
  statItem: {
    flex: 1,
  },
  statLabel: {
    fontSize: 7,
    color: '#666666',
    textTransform: 'uppercase',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  statValue: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#000000',
  },
  descriptionSection: {
    paddingTop: 12,
    borderTop: '1 solid #E5E7EB',
    marginBottom: 12,
  },
  descriptionTitle: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#333333',
    marginBottom: 6,
  },
  descriptionText: {
    fontSize: 8,
    color: '#666666',
    lineHeight: 1.6,
  },
  tagsSection: {
    paddingTop: 12,
    borderTop: '1 solid #E5E7EB',
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    fontSize: 7,
    color: '#333333',
  },
  
  // AI Usage Section
  aiUsageBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  aiUsageGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  aiUsageCard: {
    flex: 1,
    borderRadius: 8,
    padding: 14,
  },
  whisperCard: {
    backgroundColor: '#4F46E5',
  },
  gptCard: {
    backgroundColor: '#4F46E5',
  },
  totalCostCard: {
    backgroundColor: '#10B981',
  },
  aiCardTitle: {
    fontSize: 8,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  aiCardDetail: {
    fontSize: 7,
    color: '#FFFFFF',
    marginBottom: 3,
  },
  aiCardCost: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 4,
  },
  
  // Summary Section
  summaryBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  summaryText: {
    fontSize: 10,
    color: '#333333',
    lineHeight: 1.6,
  },
  
  // Metadata Grid (Content Type, Sentiment, Language, Frames)
  metadataGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  metadataCard: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 12,
  },
  metadataLabel: {
    fontSize: 7,
    fontWeight: 'bold',
    color: '#666666',
    textTransform: 'uppercase',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  metadataValue: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#000000',
    textTransform: 'capitalize',
  },
  
  // Analyzed Frames
  framesBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  framesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  frameItem: {
    width: '22%',
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    overflow: 'hidden',
  },
  frameImage: {
    width: '100%',
    height: 80,
    objectFit: 'cover',
  },
  frameInfo: {
    padding: 8,
    borderTop: '1 solid #E5E7EB',
  },
  frameLabel: {
    fontSize: 7,
    color: '#666666',
    fontWeight: 'bold',
    marginBottom: 2,
  },
  frameTime: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#4F46E5',
  },
  
  // Topics Section
  topicsBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  topicsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  topicTag: {
    backgroundColor: '#F3F4F6',
    border: '1 solid #E5E7EB',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    fontSize: 9,
    fontWeight: 'bold',
    color: '#333333',
  },
  
  // Key Points Section
  keyPointsBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  keyPointItem: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  keyPointNumber: {
    width: 24,
    height: 24,
    backgroundColor: '#4F46E5',
    borderRadius: 12,
    color: '#FFFFFF',
    fontSize: 9,
    fontWeight: 'bold',
    textAlign: 'center',
    paddingTop: 6,
  },
  keyPointContent: {
    flex: 1,
  },
  keyPointText: {
    fontSize: 9,
    color: '#333333',
    lineHeight: 1.6,
    marginBottom: 4,
  },
  keyPointTimestamp: {
    fontSize: 8,
    color: '#666666',
  },
  
  // Insights Section
  insightsBox: {
    backgroundColor: '#FFFFFF',
    border: '1 solid #E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  insightsText: {
    fontSize: 9,
    color: '#333333',
    lineHeight: 1.6,
  },
  
  // Footer
  footer: {
    position: 'absolute',
    bottom: 30,
    left: 40,
    right: 40,
    textAlign: 'center',
    fontSize: 8,
    color: '#999999',
  },
});

interface PDFDocumentProps {
  job: Job;
}

export const JobPDFDocument: React.FC<PDFDocumentProps> = ({ job }) => {
  const formatDate = (date: string | null) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDateShort = (date: string | null) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatNumber = (num: number | null) => {
    if (num === null || num === undefined) return '0';
    return num.toLocaleString('en-US');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const analysis = job.analysis?.summary;
  const aiUsage = job.analysis?.ai_usage;
  const frames = analysis?.frames || [];

  return (
    <Document>
      {/* Page 1: Header, Job Info, Video Information */}
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <SmartText style={styles.reportTitle}>Video Analysis Report</SmartText>
          <SmartText style={styles.reportSubtitle}>
            Generated on {formatDate(new Date().toISOString())}
          </SmartText>
        </View>

        {/* Job Information */}
        <View style={styles.jobInfoBox}>
          <View style={styles.jobInfoRow}>
            <SmartText style={styles.jobInfoLabel}>Job ID:</SmartText>
            <SmartText style={styles.jobInfoValue}>{job.id}</SmartText>
          </View>
          <View style={styles.jobInfoRow}>
            <SmartText style={styles.jobInfoLabel}>Video URL:</SmartText>
            <SmartText style={styles.jobInfoValue}>{job.youtube_url}</SmartText>
          </View>
          <View style={styles.jobInfoRow}>
            <SmartText style={styles.jobInfoLabel}>Created:</SmartText>
            <SmartText style={styles.jobInfoValue}>{formatDate(job.created_at)}</SmartText>
          </View>
        </View>

        {/* Video Information (YouTube Metadata) */}
        {(job.video_title || job.channel_title || job.thumbnail_url) && (
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Video Information</SmartText>
            <View style={styles.videoInfoBox}>
              {job.thumbnail_url && (
                <Image
                  src={job.thumbnail_url}
                  style={styles.thumbnail}
                />
              )}
              <View style={styles.videoInfoContent}>
                {job.video_title && (
                  <SmartText style={styles.videoTitle}>{job.video_title}</SmartText>
                )}
                
                {job.channel_title && (
                  <SmartText style={styles.channelInfo}>Channel: {job.channel_title}</SmartText>
                )}

                {job.published_at && (
                  <SmartText style={styles.publishedInfo}>
                    Published {formatDateShort(job.published_at)}
                  </SmartText>
                )}

                <View style={styles.statsGrid}>
                  {job.view_count !== null && (
                    <View style={styles.statItem}>
                      <SmartText style={styles.statLabel}>Views</SmartText>
                      <SmartText style={styles.statValue}>{formatNumber(job.view_count)}</SmartText>
                    </View>
                  )}
                  {job.like_count !== null && (
                    <View style={styles.statItem}>
                      <SmartText style={styles.statLabel}>Likes</SmartText>
                      <SmartText style={styles.statValue}>{formatNumber(job.like_count)}</SmartText>
                    </View>
                  )}
                  {job.comment_count !== null && (
                    <View style={styles.statItem}>
                      <SmartText style={styles.statLabel}>Comments</SmartText>
                      <SmartText style={styles.statValue}>{formatNumber(job.comment_count)}</SmartText>
                    </View>
                  )}
                  {job.video_duration && (
                    <View style={styles.statItem}>
                      <SmartText style={styles.statLabel}>Duration</SmartText>
                      <SmartText style={styles.statValue}>{formatDuration(job.video_duration)}</SmartText>
                    </View>
                  )}
                </View>

                {job.description && (
                  <View style={styles.descriptionSection}>
                    <SmartText style={styles.descriptionTitle}>Description</SmartText>
                    <SmartText style={styles.descriptionText}>{job.description}</SmartText>
                  </View>
                )}

                {job.tags && job.tags.length > 0 && (
                  <View style={styles.tagsSection}>
                    <SmartText style={styles.descriptionTitle}>Tags</SmartText>
                    <View style={styles.tagsContainer}>
                      {job.tags.map((tag, index) => (
                        <SmartText key={index} style={styles.tag}>{tag}</SmartText>
                      ))}
                    </View>
                  </View>
                )}
              </View>
            </View>
          </View>
        )}

        <SmartText style={styles.footer} render={({ pageNumber }: { pageNumber: number }) => `Page ${pageNumber}`} fixed />
      </Page>

      {/* Page 2: AI Usage & Summary & Metadata */}
      <Page size="A4" style={styles.page}>
        {/* AI Usage & Cost */}
        {aiUsage && (
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>AI Usage & Cost</SmartText>
            <View style={styles.aiUsageBox}>
              <View style={styles.aiUsageGrid}>
                {/* Whisper Card */}
                <View style={[styles.aiUsageCard, styles.whisperCard]}>
                  <SmartText style={styles.aiCardTitle}>Audio Transcription</SmartText>
                  <SmartText style={styles.aiCardDetail}>Model: {aiUsage.whisper_model}</SmartText>
                  <SmartText style={styles.aiCardDetail}>Duration: {aiUsage.whisper_duration_seconds}s</SmartText>
                  <SmartText style={styles.aiCardCost}>${aiUsage.whisper_cost_usd.toFixed(4)}</SmartText>
                </View>

                {/* GPT Card */}
                <View style={[styles.aiUsageCard, styles.gptCard]}>
                  <SmartText style={styles.aiCardTitle}>Video Analysis</SmartText>
                  <SmartText style={styles.aiCardDetail}>Model: {aiUsage.gpt_model}</SmartText>
                  <SmartText style={styles.aiCardDetail}>Tokens: {formatNumber(aiUsage.gpt_total_tokens)}</SmartText>
                  <SmartText style={styles.aiCardDetail}>
                    {formatNumber(aiUsage.gpt_prompt_tokens)} in · {formatNumber(aiUsage.gpt_completion_tokens)} out
                  </SmartText>
                  <SmartText style={styles.aiCardCost}>${aiUsage.gpt_cost_usd.toFixed(4)}</SmartText>
                </View>

                {/* Total Cost Card */}
                <View style={[styles.aiUsageCard, styles.totalCostCard]}>
                  <SmartText style={styles.aiCardTitle}>Total Cost</SmartText>
                  <SmartText style={styles.aiCardCost}>${aiUsage.total_cost_usd.toFixed(4)}</SmartText>
                  <SmartText style={styles.aiCardDetail}>Estimated USD</SmartText>
                </View>
              </View>
            </View>
          </View>
        )}

        {/* Summary */}
        {analysis && (
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Summary</SmartText>
            <View style={styles.summaryBox}>
              <SmartText style={styles.summaryText}>{analysis.summary}</SmartText>
            </View>
          </View>
        )}

        {/* Metadata Grid */}
        {analysis && (
          <View style={styles.section}>
            <View style={styles.metadataGrid}>
              <View style={styles.metadataCard}>
                <SmartText style={styles.metadataLabel}>Content Type</SmartText>
                <SmartText style={styles.metadataValue}>{analysis.content_type}</SmartText>
              </View>
              <View style={styles.metadataCard}>
                <SmartText style={styles.metadataLabel}>Sentiment</SmartText>
                <SmartText style={styles.metadataValue}>{analysis.sentiment}</SmartText>
              </View>
              <View style={styles.metadataCard}>
                <SmartText style={styles.metadataLabel}>Language</SmartText>
                <SmartText style={styles.metadataValue}>{analysis.language}</SmartText>
              </View>
              <View style={styles.metadataCard}>
                <SmartText style={styles.metadataLabel}>Frames Analyzed</SmartText>
                <SmartText style={styles.metadataValue}>{job.frames_count || 0}</SmartText>
              </View>
            </View>
          </View>
        )}

        <SmartText style={styles.footer} render={({ pageNumber }: { pageNumber: number }) => `Page ${pageNumber}`} fixed />
      </Page>

      {/* Page 3: Analyzed Frames */}
      {frames.length > 0 && (
        <Page size="A4" style={styles.page}>
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Analyzed Frames</SmartText>
            <View style={styles.framesBox}>
              <View style={styles.framesGrid}>
                {frames.slice(0, 16).map((frame, index) => (
                  <View key={index} style={styles.frameItem}>
                    <Image
                      src={frame.path}
                      style={styles.frameImage}
                    />
                    <View style={styles.frameInfo}>
                      <SmartText style={styles.frameLabel}>Frame {index + 1}</SmartText>
                      <SmartText style={styles.frameTime}>{formatTime(frame.timestamp)}</SmartText>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          </View>

          <SmartText style={styles.footer} render={({ pageNumber }: { pageNumber: number }) => `Page ${pageNumber}`} fixed />
        </Page>
      )}

      {/* Continue with more frames if needed */}
      {frames.length > 16 && (
        <Page size="A4" style={styles.page}>
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Analyzed Frames (continued)</SmartText>
            <View style={styles.framesBox}>
              <View style={styles.framesGrid}>
                {frames.slice(16, 32).map((frame, index) => (
                  <View key={index} style={styles.frameItem}>
                    <Image
                      src={frame.path}
                      style={styles.frameImage}
                    />
                    <View style={styles.frameInfo}>
                      <SmartText style={styles.frameLabel}>Frame {index + 17}</SmartText>
                      <SmartText style={styles.frameTime}>{formatTime(frame.timestamp)}</SmartText>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          </View>

          <SmartText style={styles.footer} render={({ pageNumber }: { pageNumber: number }) => `Page ${pageNumber}`} fixed />
        </Page>
      )}

      {/* Page: Topics & Key Points */}
      {analysis && (
        <Page size="A4" style={styles.page}>
          {/* Topics */}
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Topics</SmartText>
            <View style={styles.topicsBox}>
              <View style={styles.topicsContainer}>
                {analysis.topics.map((topic, index) => (
                  <SmartText key={index} style={styles.topicTag}>{topic}</SmartText>
                ))}
              </View>
            </View>
          </View>

          {/* Key Points */}
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Key Points</SmartText>
            <View style={styles.keyPointsBox}>
              {analysis.key_points.map((point, index) => (
                <View key={index} style={styles.keyPointItem}>
                  <SmartText style={styles.keyPointNumber}>{index + 1}</SmartText>
                  <View style={styles.keyPointContent}>
                    <SmartText style={styles.keyPointText}>{point.point}</SmartText>
                    {point.timestamp !== "N/A" && (
                      <SmartText style={styles.keyPointTimestamp}>{point.timestamp}</SmartText>
                    )}
                  </View>
                </View>
              ))}
            </View>
          </View>

          <SmartText style={styles.footer} render={({ pageNumber }: { pageNumber: number }) => `Page ${pageNumber}`} fixed />
        </Page>
      )}

      {/* Page: Detailed Insights */}
      {analysis && (
        <Page size="A4" style={styles.page}>
          <View style={styles.section}>
            <SmartText style={styles.sectionTitle}>Detailed Insights</SmartText>
            <View style={styles.insightsBox}>
              <SmartText style={styles.insightsText}>{analysis.insights}</SmartText>
            </View>
          </View>

          <SmartText style={styles.footer} render={({ pageNumber }: { pageNumber: number }) => `Page ${pageNumber}`} fixed />
        </Page>
      )}
    </Document>
  );
};
