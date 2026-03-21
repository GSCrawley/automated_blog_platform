import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { blogApi } from '@/services/api';

const ConversationalEditor = ({ article, onContentUpdate }) => {
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState('');

  const handleSubmit = async () => {
    if (!instruction.trim()) return;

    setLoading(true);
    setResponse('');

    try {
      const data = await blogApi.conversationalEdit(article.id, {
        command: instruction,
      });

      if (data.success) {
        setResponse('Changes applied successfully.');
        onContentUpdate(data.article.content, data.article.title);
      } else {
        setResponse('Error: ' + data.error);
      }
    } catch (error) {
      setResponse('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Conversational Editor</CardTitle>
          <CardDescription>
            Describe the changes you want to make to the article in natural language.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="instruction">Instruction</Label>
              <Textarea
                id="instruction"
                placeholder="e.g., Make the introduction more engaging, add a section about benefits, or rewrite the conclusion..."
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                rows={4}
              />
            </div>
            <Button onClick={handleSubmit} disabled={loading || !instruction.trim()}>
              {loading ? 'Processing...' : 'Apply Changes'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {response && (
        <Card>
          <CardHeader>
            <CardTitle>Updated Content Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: response.replace(/\n/g, '<br>') }} />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ConversationalEditor;