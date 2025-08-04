import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const UiTest = () => {
  const testData = [
    { id: 1, name: 'Test Product', price: 99.99, category: 'Test Category' }
  ];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">UI Components Test</h1>
      
      <div className="flex gap-4">
        <Button>Primary Button</Button>
        <Button variant="outline">Outline Button</Button>
        <Badge>Test Badge</Badge>
      </div>

      <Input placeholder="Test input..." className="max-w-sm" />

      <Card>
        <CardHeader>
          <CardTitle>Test Card</CardTitle>
          <CardDescription>Testing card component rendering</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Card content is working!</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Test Table</CardTitle>
          <CardDescription>Testing table component rendering</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Price</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {testData.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell>${item.price}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default UiTest;
